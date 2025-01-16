import smartpy as sp

@sp.module
def main():
    class TCGContract(sp.Contract):

        joinTCG_type : type = sp.record(userAddress = sp.address, pseudonym = sp.string, cards = sp.big_map({}), lastRedeemed = sp.timestamp)

        def __init__(self):
            self.data.cards = sp.big_map({}) # collection id
            sp.cast(self.data.cards,sp.big_map[sp.int, sp.record(title=sp.string, description=sp.string, rarety=sp.int)])
            self.data.users= sp.big_map({}) #user's address, user's pseudonym, big map user's cards blockchain id, lastRedeemed
            self.data.trades = sp.big_map({}) # Trade id, 2 address, 2 card blockchain id, timer, boolean for accept
            self.data.market = sp.big_map({}) # Sell id, address seller, price, card blockchain id
            self.data.priceBooster = sp.tez(5)

        @sp.entrypoint
        def joinUser(self, user):
            assert not self.data.users.contains(user.userAddress), "User already in the game"
            sp.cast(user, joinTCG_type)
            self.data.users[user.userAddress] = user

        @sp.entrypoint
        def generateFreeBooster(self):
            pass

        @sp.entrypoint
        def generatePaidBooster(self):
            pass
            
        @sp.onchain_view
        def getCardbyId(self, blockchainCardId):
            return self.data.cards[blockchainCardId]

        @sp.onchain_view
        def getCardsbyUser(self, userAddress):
            return self.data.users[userAddress].cards

        @sp.entrypoint
        def exchangeCard(self, userAddress1, userAddress2, blockchainCardId1, blockchainCardId2):
            #call UI
            #add to trade big_map
            #call process
            pass

        @sp.entrypoint
        def processExchange(self, tradeId):
            #check if users have their cards
            #check timer
            #switch owner + 1 tez for fee
            pass

        @sp.entrypoint
        def sellCard(self, userAddress, blockchainCardId, price):
            assert self.data.users[userAddress].cards[blockchainCardId], "User doesn't have this card"
            self.data.market[blockchainCardId] = sp.record(
                seller = userAddress,
                price = price,
                cardId = blockchainCardId
            )

        @sp.entrypoint
        def buyCard(self, userAddress, sellId):
            #check if user has enough tez + fee
            #switch owner
            # remove from market
            pass      

    class UserContract(sp.Contract):

        joinTCG_type : type = sp.record(userAddress = sp.address, pseudonym = sp.string, cards = sp.big_map({}), lastRedeemed = sp.timestamp)

        def __init__(self,tcgContract):
            self.data.TCGContract = tcgContract

        @sp.entrypoint
        def joinTCG(self, pseudonym):
            # give one booster free if not in users big_map
            assert sp.amount == sp.tez(1), "You must send 1 tez to join the game"
            TCGContract = sp.contract(joinTCG_type, self.data.TCGContract, entry_point="joinUser").unwrap_some()
            data = sp.record(userAddress = sp.sender, pseudonym = pseudonym, cards = sp.big_map({}), lastRedeemed = sp.now)
            sp.transfer(data, sp.tez(1), TCGContract)

        @sp.entrypoint
        def buyBooster(self):
            pass

        @sp.entrypoint
        def getFreeBooster(self):
            pass

        @sp.entrypoint
        def sellCard(self, id):
            pass

        @sp.entrypoint
        def askTrade(self, userAddress, askedBlockchainCardId, givenockchainCardId):
            pass

        @sp.entrypoint
        def acceptTrade(self):
            pass

        @sp.entrypoint
        def declineTrade(self):
            pass

        @sp.entrypoint
        def sellCard(self, blockchainCardId, price):
            pass

        @sp.entrypoint
        def buyCard(self, blockchainCardId):
            pass


        
            


@sp.add_test()
def test():
    scenario = sp.test_scenario("TezCG", main)
    scenario.h1("TezCG")

    c1 = main.TCGContract()
    scenario += c1

    c1.my_entrypoint(12)
    c1.my_entrypoint(13)
    c1.my_entrypoint(14)
    c1.my_entrypoint(50)
    c1.my_entrypoint(50)
    c1.my_entrypoint(50, _valid=False)  # this is expected to fail
    # Finally, we check its final storage
    scenario.verify(c1.data.my_parameter_1 == 151)

    # We can define another contract using the current state of c1
    c2 = main.MyContract(1, c1.data.my_parameter_1)
    scenario += c2
    scenario.verify(c2.data.my_parameter_2 == 151)
