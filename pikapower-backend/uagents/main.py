from seller import seller
from buyer import buyer
from uagents import Bureau

bureau = Bureau([seller, buyer])

if __name__ == "__main__":
    bureau.run()