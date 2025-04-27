from uagents import Agent, Model, Context
import requests
import json
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
import re
import time
import os
from dotenv import load_dotenv
from config import provider_cost, buy_amount

load_dotenv()
API_KEY = os.getenv('API_KEY')

buyer = Agent(
    "Buyer",
    seed="pika-power-buyer",
    port=8001,
    endpoint="http://localhost:8001/submit"
)

class InitialQuery(Model):
    pass

class InitialQueryResponse(BaseModel):
    price: int = Field(description="A int of your initial offer price")

class ActionTaken(BaseModel):
    action: str = Field(description="A string of the json of your return offer")

class AgreementReached(Model):
    price: int

history = []
last_offers = {}

def make_request(sellers="{}"):
    parser = PydanticOutputParser(pydantic_object=ActionTaken)
    seller_list = json.loads('[' + sellers + ']')
    for i in seller_list:
        last_offers[i["name"]] = i["offer-price"]

    prompt = f"""
    {{provider-cost: {provider_cost}, buy-amount: {buy_amount}, seller-list: [{sellers}]}}
    {parser.get_format_instructions()}
    """

    initialMessage = f"""
            For each of my inputs, the following instructions must be followed:
            Definitions:
            “Seller”: An agent on behalf of the user that is looking to sell excess power generated from their solar panels, the user has the capability to transfer this power at will.
            “Buyer”: An agent on behalf of the user that is looking to purchase power.
            “Marketplace”: A peer-to-peer platform that functions like a stock market where the buyer and seller agents bid and ask over multiple requests until a price for which to trade power is mutually agreed on.

            Operational Guidelines:
            You are the Buyer as defined earlier
            The following information will be provided to you
            The amount of power you need to buy
            A list of all the sellers, including the amount they are selling(W), their asking price(dollars).
            The cost of buying from an electricity provider, don’t pay more than this when buying from a neighbor
            Save past responses in memory
            Try to aggressively negotiate as low of an offer as possible.
            DO NOT UNDER ANY CIRCUMSTANCES ACCEPT THE FIRST OFFER YOU RECEIVE!

            An example request:
            {{"provider-cost": 40, "amount-needed": 400, "seller-list": [{{"name": "seller 1", "asking-price": 37, "sell-amount": 500}}, {{"name": "seller 2", "asking-price": 33, "sell-amount": 200}}]
            }}

            Format your response like in this example:
            {{"name": "seller 1", "buy-amount": 200, "offer-price": 35}}, {{"name": "seller 2", "buy-amount": 200, "offer-price": 32}}

            Or, if you decide to accept the current price, offer the same price as the seller asked:
            {{"name": "seller 1", "buy-amount": 200, "offer-price": 37}}, {{"name": "seller 2", "buy-amount": 200, "offer-price": 33}}

            For this first prompt, respond by saying:
            I acknowledge
            """

    global history
    messages = [
    {
    "role": "system",
    "content": "You are designed to follow instructions and think logically and objectively"
    }, 
    {
    "role": "user",
    "content": initialMessage
    },
    {
    "role": "assistant",
    "content": "I acknowledge"
    },
    *history,
    {
    "role": "user",
    "content": prompt
    }]


    url = "https://api.asi1.ai/v1/chat/completions"

    payload = json.dumps({
    "model": "asi1-mini",
    "messages": messages,
    "temperature": 0.5,
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
                    if parsed_output.action:
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


@buyer.on_message(model=ActionTaken)
async def handle_message(ctx: Context, sender, message: ActionTaken):
    ctx.logger.info(message.action)
    action_taken = make_request(message.action)
    await ctx.send(sender, action_taken)

@buyer.on_message(model=InitialQueryResponse)
async def handle_message(ctx: Context, sender, message: InitialQueryResponse):
    ctx.logger.info(f"price received:{message.price}")
    action_taken = make_request(f'{{"name": "seller 1", "offer-price": {message.price}, "buy-amount": {buy_amount}}}')
    await ctx.send(sender, action_taken)
    
@buyer.on_message(model=AgreementReached)
async def handle_agreementReached(ctx: Context, sender, message: AgreementReached):
    ctx.logger.info(f"Agreement Reached: {message.price}")

@buyer.on_event("startup")
async def send_message(ctx: Context):
    await ctx.send('agent1qf8dwh5kfgra5n2r9nnrvv8yumdmrj7zuqqsryd77ws9khtunxry2uajggq', InitialQuery())
    ctx.logger.info(f"Initial request has been sent to Seller")


