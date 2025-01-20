import smartpy as sp

@sp.module
def main():

    joinTCG_type : type = sp.record(userAddress = sp.address, pseudonym = sp.string, cards = sp.big_map[sp.int,sp.int], lastRedeemed = sp.timestamp)
    generate_type : type = sp.address
    
    class TCGContract(sp.Contract):

        def __init__(self, owner, address_contract_oracle):
            self.data.owner = owner
            self.data.address_contract_oracle = address_contract_oracle
            self.data.cards = sp.big_map({}) # collection id
            self.data.nbcard = 0
            sp.cast(self.data.cards,sp.big_map[sp.int, sp.record(title=sp.string, description=sp.string, rarety=sp.int)])
            self.data.users= sp.big_map({}) #user's address, user's pseudonym, big map user's cards blockchain id, lastRedeemed
            self.data.trades = sp.big_map({}) # Trade id, 2 address, 2 card blockchain id, timer, boolean for accept
            self.data.market = sp.big_map({}) # Sell id, address seller, price, card blockchain id
            self.data.priceBooster = sp.tez(5)
            self.data.action = 0
            self.data.sellfee = sp.tez(2)

        @sp.entrypoint
        def joinUser(self, user):
            self.data.action +=1
            assert not self.data.users.contains(user.userAddress), "User already in the game"
            sp.cast(user, joinTCG_type)
            self.data.users[user.userAddress] = user

        @sp.entrypoint
        def generateFreeBooster(self,player_address):
            self.data.action +=1
            # number that change for call every entrypoints on this contract + randomness oracle + maybe more
            assert self.data.users.contains(player_address), "You need to JoinTCg Before"
            player = self.data.users[player_address]
            assert sp.now > sp.add_days(player.lastRedeemed, 1), "You need to wait 1 days for new user to have free booster or you can only 1 booster free by days"
            random_seed = sp.view("get_random", self.data.address_contract_oracle,(),sp.int).unwrap_some()
            for i in range(4):
                 self.data.action +=1
                 random_index = sp.to_int(sp.mod((random_seed + i + self.data.action),self.data.nbcard))
                 card_id = self.data.cards.contains(random_index)
                 assert card_id , "Error occured with random value"
                 if not player.cards.contains(random_index):
                     player.cards[random_index] = 1
                 else:
                    player.cards[random_index] += 1
            player.lastRedeemed = sp.now
            self.data.users[player_address] = player

        @sp.entrypoint
        def generatePaidBooster(self,player_address):
            self.data.action +=1
            # number that change for call every entrypoints on this contract + randomness oracle + maybe more
            assert self.data.users.contains(player_address), "You need to JoinTCg Before"
            player = self.data.users[player_address]
            assert sp.amount == self.data.priceBooster , "You need to paid 5 tez to have the booster"
            random_seed = sp.view("get_random", self.data.address_contract_oracle,(),sp.int).unwrap_some()
            for i in range(4):
                 self.data.action +=1
                 random_index = sp.to_int(sp.mod((random_seed + i + self.data.action),self.data.nbcard))
                 card_id = self.data.cards.contains(random_index)
                 assert card_id , "Error occured with random value"
                 if not player.cards.contains(random_index):
                     player.cards[random_index] = 1
                 else:
                    player.cards[random_index] += 1
            self.data.users[player_address] = player
            
        @sp.onchain_view
        def getCardbyId(self, blockchainCardId):
            return self.data.cards[blockchainCardId]

        @sp.onchain_view
        def getCardsbyUser(self, userAddress):
            return self.data.users[userAddress].cards

        @sp.entrypoint
        def exchangeCard(self, userAddress1, userAddress2, blockchainCardId1, blockchainCardId2):
            self.data.action +=1
            #call UI
            #add to trade big_map
            #call process
            pass

        @sp.entrypoint
        def processExchange(self, tradeId):
            self.data.action +=1
            #check if users have their cards
            #check timer
            #switch owner + 1 tez for fee
            pass

        @sp.entrypoint
        def sellCard(self, userAddress, blockchainCardId, price):
            self.data.action +=1
            assert self.data.users[userAddress].cards.contains(blockchainCardId), "You don't have this card"
            self.data.market[blockchainCardId] = sp.record(
                seller = userAddress,
                price = price,
                cardId = blockchainCardId
            )

        @sp.entrypoint
        def buyCard(self, userAddress, sellId):
            self.data.action +=1
            #check if user has enough tez + fee
            assert sp.amount == self.data.market[sellId].price + self.data.sellfee, "You must send the exact amount"
            #switch owner
            self.data.users[userAddress].cards[self.data.market[sellId].cardId] += 1 # modify this to get the number of card of the user becaus we can have double
            # del from seller
            if self.data.users[self.data.market[sellId].seller].cards[self.data.market[sellId].cardId] == 1:
                del self.data.users[self.data.market[sellId].seller].cards[self.data.market[sellId].cardId]
            else:
                self.data.users[self.data.market[sellId].seller].cards[self.data.market[sellId].cardId] -= 1
            # transfer tez
            sp.send(self.data.market[sellId].seller, sp.amount - self.data.sellfee)
            sp.send(self.data.owner, self.data.sellfee)
            # remove from market
            del self.data.market[sellId]
            
        @sp.entrypoint
        def get_balance_admin(self, nb_tez):
            sp.cast(nb_tez,sp.mutez)
            assert sp.sender == self.data.owner , "You are not owner"
            assert nb_tez > sp.balance , "You can get more tez that the contract contains"
            sp.send(self.data.owner,nb_tez)
            
        @sp.entrypoint
        def add_card(self,card):
            sp.cast(card,sp.record(title=sp.string, description=sp.string, rarety=sp.int))
            assert sp.sender == self.data.owner , "You are not owner"
            self.data.cards[self.data.nbcard] = card
            self.data.nbcard += 1
            
    class OracleRandom(sp.Contract):
        # add random number
        # list of oracle can modify this number 
        # verify that number it's modify every 10 sec if not bloc the generator of card
        def __init__(self, owner):
            self.data.owner = owner
            self.data.random = 0
            self.data.autorize_address = sp.big_map({}) # record with address of the oracle and activate or not 
            self.data.last_updated = sp.now

        @sp.entrypoint
        def add_address_oracle(self,address):
            assert sp.sender == self.data.owner , "You are not owner"
            assert not self.data.autorize_address.contains(address) , "This address exist already"
            self.data.autorize_address[address] = True

        @sp.entrypoint
        def del_address_oracle(self,address):
            assert sp.sender == self.data.owner , "You are not owner"
            assert self.data.autorize_address.contains(address) , "This address don't exist"
            del self.data.autorize_address[address]

        @sp.entrypoint
        def activate_address_oracle(self,address):
            assert sp.sender == self.data.owner , "You are not owner"
            assert self.data.autorize_address.contains(address) , "This address don't exist"
            self.data.autorize_address[address] = True

        @sp.entrypoint
        def deactivate_address_oracle(self,address):
            assert sp.sender == self.data.owner , "You are not owner"
            assert self.data.autorize_address.contains(address) , "This address don't exist"
            self.data.autorize_address[address] = False

        @sp.entrypoint
        def modify_random(self,random):
            assert self.data.autorize_address.contains(sp.sender) , "You can modify the random number"
            assert self.data.random != random , "It's the same number of the last random"
            assert self.data.autorize_address[sp.sender] , "this Oracle it's deactivate for the moment you can modify this number"
            self.data.random = random
            self.data.last_updated = sp.now

        @sp.onchain_view
        def get_random(self):
            assert sp.now <= sp.add_seconds(self.data.last_updated, 10),"Problem with random oracle need to wait"
            return self.data.random

        
            
    class UserContract(sp.Contract):

        def __init__(self, tcgContract):
            self.data.TCGContract = tcgContract

        @sp.entrypoint
        def joinTCG(self, pseudonym):
            # give one booster free if not in users big_map
            assert sp.amount == sp.tez(1), "You must send 1 tez to join the game"
            tcgcontract = sp.contract(joinTCG_type, self.data.TCGContract, entrypoint="joinUser").unwrap_some()
            data = sp.record(userAddress = sp.sender, pseudonym = pseudonym, cards = sp.big_map({}), lastRedeemed = sp.now)
            sp.transfer(data, sp.tez(1), tcgcontract)

        @sp.entrypoint
        def buyBooster(self):
            tcgcontract = sp.contract(generate_type, self.data.TCGContract, entrypoint="generatePaidBooster").unwrap_some()
            sp.transfer(sp.sender, sp.amount, tcgcontract)

        @sp.entrypoint
        def getFreeBooster(self):
            tcgcontract = sp.contract(generate_type, self.data.TCGContract, entrypoint="generateFreeBooster").unwrap_some()
            sp.transfer(sp.sender, sp.tez(0), tcgcontract)

        @sp.entrypoint
        def sellCard(self, id, price):
            # this don't work
            """
            tcgcontract = sp.contract(sp.TUnit, self.data.TCGContract, entrypoint="sellCard").unwrap_some()
            sp.transfer(sp.record(userAddress = sp.sender, blockchainCardId = id, price = price), sp.tez(0), tcgcontract)
            """
            
        @sp.entrypoint
        def buyCard(self, id):
            # this don't work
            """
            tcgcontract = sp.contract(sp.TUnit, self.data.TCGContract, entrypoint="buyCard").unwrap_some()
            sp.transfer(sp.record(userAddress = sp.sender, sellId = id), sp.tez(0), tcgcontract)
            """
        @sp.entrypoint
        def askTrade(self, userAddress, askedBlockchainCardId, givenockchainCardId):
            pass

        @sp.entrypoint
        def acceptTrade(self):
            pass

        @sp.entrypoint
        def declineTrade(self):
            pass
            

#Test oracle with generate Card
@sp.add_test()
def test_oracle():
    scenario = sp.test_scenario("Test oracle with generate Card", main)
    alice = sp.test_account("alice").address
    bob = sp.test_account("bob").address
    toto = sp.test_account("toto").address
    random = sp.test_account("random").address
    random_2= sp.test_account("random_2").address
    
    scenario.h1("Test oracle with generate Card")
    c3 = main.OracleRandom(alice)
    c1 = main.TCGContract(alice,c3.address)
    c2 = main.UserContract(c1.address)
    
    scenario += c1
    scenario += c2
    scenario += c3

    scenario.h2("Create card for the beginning of the game")
    c2.joinTCG("test",_sender=bob,_amount=sp.tez(1),_now=sp.timestamp_from_utc(2025,1,16,15,38,0))
    c1.add_card(sp.record(title="Dragon de Feu", description="Capable de réduire ses ennemis en cendres en un souffle.", rarety=5), _sender=alice)
    c1.add_card(sp.record(title="Golem de Pierre", description="Inébranlable et protecteur, une forteresse vivante.", rarety=3), _sender=alice)
    c1.add_card(sp.record(title="Sorcier Sombre", description="Manipulateur des ombres, il inspire la peur.", rarety=4), _sender=alice)
    c1.add_card(sp.record(title="Chevalier Divin", description="Un guerrier béni par les dieux eux-mêmes.", rarety=5), _sender=alice)
    c1.add_card(sp.record(title="Loup Fantôme", description="Invisible la nuit, mais mortel au combat.", rarety=2), _sender=alice)
    c1.add_card(sp.record(title="Archère Élémentaire", description="Maîtrise les flèches de feu, d'eau et de vent.", rarety=3), _sender=alice)
    c1.add_card(sp.record(title="Revenant du Néant", description="Une entité qui revient sans cesse de l'oubli.", rarety=4), _sender=alice)
    c1.add_card(sp.record(title="Mage du Temps", description="Peut ralentir ou accélérer le cours du temps.", rarety=5), _sender=alice)
    c1.add_card(sp.record(title="Slime Ancien", description="Il semble faible, mais cache un pouvoir dévastateur.", rarety=1), _sender=alice)

    scenario.h2("Test with create of FreeBooster")
    c3.add_address_oracle(random,_sender=alice)
    c3.modify_random(145456446650,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))
    c2.getFreeBooster(_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))

    scenario.h2("Test with create of FreeBooster 10 min after already get my FreeBooster (Error)")
    c3.modify_random(14545644650,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0))
    c2.getFreeBooster(_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_valid=False,_exception='You need to wait 1 days for new user to have free booster or you can only 1 booster free by days')

    scenario.h2("Test with create of FreeBooster with Player don't join the game (Error)")
    c3.modify_random(14545644654,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0))
    c2.getFreeBooster(_sender=toto,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_valid=False,_exception='You need to JoinTCg Before')

    scenario.h2("Test with create of buyBooster")
    c3.modify_random(14545644651,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0))
    c2.buyBooster(_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_amount=sp.tez(5))

    scenario.h2("Test with create of buyBooster with amount")
    c3.modify_random(14545644641,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0))
    c2.buyBooster(_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_amount=sp.tez(1),_valid=False,_exception='You need to paid 5 tez to have the booster')

    scenario.h2("Test with create of buyBooster with Player don't join the game (Error)")
    c3.modify_random(1454564654,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0))
    c2.getFreeBooster(_sender=toto,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_valid=False,_exception='You need to JoinTCg Before')

    scenario.h2("Test with create of buyBooster with oracle don't send data before 10 sec (Error)")
    c3.modify_random(1454564657,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0))
    c2.buyBooster(_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,49,11),_valid=False,_amount=sp.tez(5),_exception='Problem with random oracle need to wait')

    scenario.h2("oracle send the same random (Error)")
    c3.modify_random(1454564657,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_valid=False,_exception="It's the same number of the last random")

    
    scenario.h2("Deactivate Oracle")
    c3.deactivate_address_oracle(random,_sender=alice)
    scenario.verify(c3.data.autorize_address[random] == False)

    scenario.h2("oracle send the random but it's deactivate (Error)")
    c3.modify_random(145456467,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_valid=False,_exception="this Oracle it's deactivate for the moment you can modify this number")

    scenario.h2("activate Oracle")
    c3.activate_address_oracle(random,_sender=alice)
    scenario.verify(c3.data.autorize_address[random] == True)

    scenario.h2("Deactivate Oracle with wrong address (Error)")
    c3.deactivate_address_oracle(random_2,_sender=alice,_valid=False,_exception="This address don't exist")

    scenario.h2("activate Oracle with wrong address (Error)")
    c3.activate_address_oracle(random_2,_sender=alice,_valid=False,_exception="This address don't exist")

    scenario.h2("deleted Oracle")
    c3.del_address_oracle(random,_sender=alice)

    scenario.h2("oracle send the random but it's deleted (Error)")
    c3.modify_random(145456467,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,49,0),_valid=False,_exception="You can modify the random number")

    scenario.h2("deleted Oracle  with wrong address (Error)")
    c3.del_address_oracle(random_2,_sender=alice,_valid=False,_exception="This address don't exist")

    scenario.h2("add Oracle with not owner user (Error)")
    c3.add_address_oracle(random,_sender=bob,_valid=False,_exception='You are not owner')



    
#Test for selling
@sp.add_test()
def test():
    scenario = sp.test_scenario("TezCG", main)
    alice = sp.test_account("alice").address
    bob = sp.test_account("bob").address
    random = sp.test_account("random").address
    
    scenario.h1("TezCG")
    c3 = main.OracleRandom(alice)
    c1 = main.TCGContract(alice,c3.address)
    c2 = main.UserContract(c1.address)
    
    scenario += c1
    scenario += c2
    scenario += c3


    c2.joinTCG("test",_sender=bob,_amount=sp.tez(1),_now=sp.timestamp_from_utc(2025,1,16,15,38,0))
    c1.add_card(sp.record(title="Dragon de Feu", description="Capable de réduire ses ennemis en cendres en un souffle.", rarety=5), _sender=alice)
    c1.add_card(sp.record(title="Golem de Pierre", description="Inébranlable et protecteur, une forteresse vivante.", rarety=3), _sender=alice)
    c1.add_card(sp.record(title="Sorcier Sombre", description="Manipulateur des ombres, il inspire la peur.", rarety=4), _sender=alice)
    c1.add_card(sp.record(title="Chevalier Divin", description="Un guerrier béni par les dieux eux-mêmes.", rarety=5), _sender=alice)
    c1.add_card(sp.record(title="Loup Fantôme", description="Invisible la nuit, mais mortel au combat.", rarety=2), _sender=alice)
    c1.add_card(sp.record(title="Archère Élémentaire", description="Maîtrise les flèches de feu, d'eau et de vent.", rarety=3), _sender=alice)
    c1.add_card(sp.record(title="Revenant du Néant", description="Une entité qui revient sans cesse de l'oubli.", rarety=4), _sender=alice)
    c1.add_card(sp.record(title="Mage du Temps", description="Peut ralentir ou accélérer le cours du temps.", rarety=5), _sender=alice)
    c1.add_card(sp.record(title="Slime Ancien", description="Il semble faible, mais cache un pouvoir dévastateur.", rarety=1), _sender=alice)

    c3.add_address_oracle(random,_sender=alice)
    c3.modify_random(145456446650,_sender=random,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))
    c2.getFreeBooster(_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))

    """
    #test for selling / buying card
    c2.sellCard(0,sp.tez(10),_sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))
    c2.buyCard(0,_sender=alice,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))
    """
