from uagents import Agent, Model, Context
import requests
import json
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
import re
import time
import os
from dotenv import load_dotenv
from config import provider_cost, sell_amount

load_dotenv()
API_KEY = os.getenv('API_KEY')

seller = Agent(
    name="Seller",
    seed="pika-power-seller",
    port=8000,
    endpoint="http://localhost:8000/submit"
)

class InitialQuery(Model):
    pass

class InitialQueryResponse(BaseModel):
    price: int = Field(description="A int of your initial offer price")

class ActionTaken(BaseModel):
    action: str = Field(description="A string of the json of your return offer")

class AgreementReached(Model):
    price: int

initial_price = InitialQueryResponse(price=provider_cost)
history = []
last_offers = {}

def make_request(model, buyers="{}"):
    parser = PydanticOutputParser(pydantic_object=model)
    if (model == ActionTaken):
        buyer_list = json.loads('[' + buyers + ']')
        for i in buyer_list:
            last_offers[i["name"]] = i["offer-price"]

    prompt = f"""
    {{provider-cost: {provider_cost}, excess-avaliable: {sell_amount}, buyer-list: [{buyers}]}}
    """

    initialMessage = f"""
            For each of my inputs, the following instructions must be followed:
            Definitions:
            “Seller”: An agent on behalf of the user that is looking to sell excess power generated from their solar panels, the user has the capability to transfer this power at will.
            “Buyer”: An agent on behalf of the user that is looking to purchase power.
            “Marketplace”: A peer-to-peer platform that functions like a stock market where the buyer and seller agents bid and ask over multiple requests until a price for which to trade power is mutually agreed on.

            Operational Guidelines:
            You are the Seller as defined earlier
            The following information will be provided to you
            The amount of power you have to sell
            The cost of buying from an electricity provider, price your power competitively so you can sell
            You cannot make an offer directly to the buyer but whenever a buyer makes an offer to you, you can see the following information
            How much power they want to buy
            How much they are offering per unit price
            You can use this information to change your offer
            At the beginning, you must decide on an initial price based on the cost of buying from an electricity provider and the amount of electricity you have.
            Right now, the electricity provider cost is {provider_cost} and you have {sell_amount} power
            Save past responses in memory
            Try to negotiate as high of an offer as possible, however, always finish the deal within 5 turns. Keep track of the chat history
            
            An example request:
            {{"name": "buyer 1", "buy-amount": 500, "offer-price": 30}}

            Format your response like in this example:

            Or, if you decide to accept the current price, offer the same price as the buyer bid:
            {{"name": "buyer 1", "sell-amount": 500, "offer-price": 30}}

            You can also choose to offer a lower sell-amount to the buyer:
            {{"name": "buyer 1", "sell-amount": 200, "offer-price": 30}}

            For this first prompt, respond by saying:
            (initial offering price)
            For example:
            35
            """
    
    if (model == InitialQueryResponse):
        initialMessage += parser.get_format_instructions()
    else:
        prompt += parser.get_format_instructions()

    messages = [
    {
    "role": "system",
    "content": "You are designed to follow instructions and think logically and objectively"
    }, 
    {
    "role": "user",
    "content": initialMessage
    }]

    global history
    if (model == ActionTaken):
        messages += [{
        "role": "assistant",
        "content": f"I acknowledge {initial_price}"
        }, *history,
        {
        "role": "user",
        "content": prompt
        }]


    url = "https://api.asi1.ai/v1/chat/completions"

    payload = json.dumps({
    "model": "asi1-mini",
    "messages": messages,
    "temperature": 0.2,
    "stream": False,
    "max_tokens": 500
    })

    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
    }

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            result = json.loads(response.text)
            if 'choices' in result and len(result['choices']) > 0:
                llm_response = result['choices'][0]['message']['content']
                try:
                    parsed_output = parser.parse(llm_response)
                    if model == ActionTaken and parsed_output.action:
                        i = json.loads(parsed_output.action)
                        if(last_offers[i["name"]] == i["offer-price"]):
                            return AgreementReached(price=i["offer-price"])
                    if parsed_output:
                        history.append({
                            "role": "user",
                            "content": prompt
                        })
                        history.append({
                            "role": "assistant",
                            "content": llm_response
                        })
                        return parsed_output
                    else:
                        print(f"Error: {parsed_output.action}")
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"Retrying... (Attempt {retry_count + 1}/{max_retries})")
                except Exception as e:
                    print(f"Failed to parse response with LangChain parser: {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Retrying... (Attempt {retry_count + 1}/{max_retries})")
                        time.sleep(1)
            else:
                print("Raw response:", response.text)
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(1)
        except json.JSONDecodeError:
            print("Failed to parse response as JSON.")
            print("Raw response:", response.text)
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(1)

@seller.on_message(model=InitialQuery)
async def handle_initialQuery(ctx: Context, sender, message: InitialQuery):
    global initial_price
    initial_price = make_request(InitialQueryResponse)
    await ctx.send(sender, initial_price)

@seller.on_message(model=ActionTaken)
async def handle_actionTaken(ctx: Context, sender, message: ActionTaken):
    ctx.logger.info(message.action)
    action_taken = make_request(ActionTaken, message.action)
    await ctx.send(sender, action_taken)

@seller.on_message(model=AgreementReached)
async def handle_agreementReached(ctx: Context, sender, message: AgreementReached):
    ctx.logger.info(f"Agreement Reached: {message.price}")