import smartpy as sp

@sp.module
def main():

    joinTCG_type : type = sp.record(userAddress = sp.address, pseudonym = sp.string, cards = sp.big_map[sp.int,sp.int], lastRedeemed = sp.timestamp)
    generate_type : type = sp.address
    sellCard_type : type = sp.record(userAddress = sp.address, cardId = sp.int, price = sp.mutez)
    buyCard_type : type = sp.record(userAddress = sp.address, sellId = sp.int)
    exchangeCard_type : type = sp.record(userAddress1 = sp.address, userAddress2 = sp.address, cardId1 = sp.int, cardId2 = sp.int)
    acceptTrade_type : type = sp.record(tradeId = sp.int, userAddress = sp.address)
    declineTrade_type : type = sp.record(tradeId = sp.int, userAddress = sp.address)
    processExchange_type : type = sp.int
    
    class TCGContract(sp.Contract):

        def __init__(self, owner, address_contract_oracle):
            self.data.owner = owner
            self.data.address_contract_oracle = address_contract_oracle
            self.data.modify_address_contract_user = False
            self.data.address_contract_user = sp.address("0")
            self.data.cards = sp.big_map({}) # collection id
            self.data.nbcard = 0
            sp.cast(self.data.cards,sp.big_map[sp.int, sp.record(title=sp.string, description=sp.string, rarety=sp.int)])
            self.data.users= sp.big_map({}) #user's address, user's pseudonym, big map user's cards id, lastRedeemed
            self.data.trades = sp.big_map({}) # Trade id, 2 address, 2 card id, timer, boolean for accept
            self.data.market = sp.big_map({}) # Sell id, address seller, price, card id
            self.data.balance = sp.big_map({})
            self.data.priceBooster = sp.tez(5)
            self.data.action = 0
            self.data.sellfee = sp.tez(2)
            self.data.sellId = 0
            self.data.tradeId = 0

        @sp.entrypoint
        def add_address_contract_User(self, address_contract_User):
            assert sp.sender == self.data.owner , "You are not owner"
            assert not self.data.modify_address_contract_user ,"You can modify only one time"
            self.data.address_contract_user = address_contract_User
            self.data.modify_address_contract_user = True

        @sp.entrypoint
        def joinUser(self, user):
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            self.data.action +=1
            assert not self.data.users.contains(user.userAddress), "User already in the game"
            sp.cast(user, joinTCG_type)
            self.data.users[user.userAddress] = user

        @sp.entrypoint
        def generateFreeBooster(self,player_address):
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
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
        def generatePaidBooster(self, player_address):
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
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
        def getCardbyId(self, cardId):
            return self.data.cards[cardId]

        @sp.onchain_view
        def getCardsbyUser(self, userAddress):
            return self.data.users[userAddress].cards

        @sp.entrypoint
        def exchangeCard(self, userAddress1, userAddress2, cardId1, cardId2):
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            self.data.action += 1
            assert self.data.users.contains(userAddress1), "You need to JoinTCg Before"
            assert self.data.users.contains(userAddress2), "Your trade partner need to JoinTCg Before"
            player1 = self.data.users[userAddress1]
            assert player1.cards.contains(cardId1), "You need to have the card that you want to trade"
            player2 = self.data.users[userAddress2]
            assert player2.cards.contains(cardId2), "Your trade partner need to have the card that you want to have from him"
            self.data.trades[self.data.tradeId] = sp.record(
                userAddress1 = userAddress1,
                userAddress2 = userAddress2,
                cardId1 = cardId1,
                cardId2 = cardId2,
                timer = sp.now,
                accepted = False)
            self.data.tradeId += 1

        @sp.entrypoint
        def processExchange(self, tradeId):
            assert self.data.trades.contains(tradeId), "This trade does not exist or has been refused"
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            self.data.action += 1
            assert self.data.trades[tradeId].accepted == True, "Your trade partner does not have accepted yet"
            player1 = self.data.users[self.data.trades[tradeId].userAddress1]
            player2 = self.data.users[self.data.trades[tradeId].userAddress2]
            cardId1 = self.data.trades[tradeId].cardId1
            cardId2 = self.data.trades[tradeId].cardId2
            assert player1.cards.contains(cardId1), "You need to have the card that you want to trade"
            assert player2.cards.contains(cardId2), "Your trade partner need to have the card that you want to have from him"
            
            if not player1.cards.contains(cardId2):
                player1.cards[cardId2] = 1
            else:
                player1.cards[cardId2] += 1

            if player2.cards[cardId2] == 1:
                del player2.cards[cardId2]
            else:
                player2.cards[cardId2] -= 1
                
            if not player2.cards.contains(cardId1):
                player2.cards[cardId1] = 1
            else:
                player2.cards[cardId1] += 1

            if player1.cards[cardId1] == 1:
                del player1.cards[cardId1]
            else:
                player1.cards[self.data.trades[tradeId].cardId1] -= 1

            self.data.users[self.data.trades[tradeId].userAddress1] = player1
            self.data.users[self.data.trades[tradeId].userAddress2] = player2
            
            del self.data.trades[tradeId]
            
        @sp.entrypoint
        def acceptTrade(self, tradeId, userAddress):
            assert self.data.trades.contains(tradeId), "This trade does no longer exist"
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            assert sp.add_days(self.data.trades[tradeId].timer, 1) < sp.now,  "The time limit for this trade has expired => the trade is cancelled"
            assert self.data.trades[tradeId].userAddress2 == userAddress, "You are not allowed to accept this trade"
            self.data.trades[tradeId].accepted = True
            
        @sp.entrypoint
        def declineTrade(self, tradeId, userAddress):
            assert self.data.trades.contains(tradeId), "This trade does no longer exist"
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            assert self.data.trades[tradeId].userAddress2 == userAddress, "You are not allowed to decline this trade"
            del self.data.trades[tradeId]

        @sp.entrypoint
        def sellCard(self, userAddress, cardId, price):
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            self.data.action +=1
            assert self.data.users[userAddress].cards.contains(cardId), "You don't have this card"
            self.data.market[self.data.sellId] = sp.record(
                seller = userAddress,
                price = price,
                cardId = cardId
            )
            self.data.sellId += 1

        @sp.entrypoint
        def buyCard(self, userAddress, sellId):
            assert self.data.address_contract_user == sp.sender ,"Only User_contract can interact with this endpoint"
            self.data.action +=1
            #check if user has enough tez + fee
            assert self.data.market.contains(sellId), "This card is not on the market"
            assert sp.amount == self.data.market[sellId].price + self.data.sellfee, "You must send the exact amount"
            assert self.data.users.contains(userAddress), "You must join the game before"
            #switch owner
            # if not in user's cards, add it
            if not self.data.users[userAddress].cards.contains(self.data.market[sellId].cardId):
                self.data.users[userAddress].cards[self.data.market[sellId].cardId] = 1
            else:
                # if user already has this card, increment
                self.data.users[userAddress].cards[self.data.market[sellId].cardId] += 1
            # del from seller
            if self.data.users[self.data.market[sellId].seller].cards[self.data.market[sellId].cardId] == 1:
                del self.data.users[self.data.market[sellId].seller].cards[self.data.market[sellId].cardId]
            else:
                self.data.users[self.data.market[sellId].seller].cards[self.data.market[sellId].cardId] -= 1
            # transfer tez
            # sp.send(self.data.market[sellId].seller, sp.amount - self.data.sellfee)
            if not self.data.balance.contains(self.data.market[sellId].seller):
                self.data.balance[self.data.market[sellId].seller] = sp.amount - self.data.sellfee
            else:
                self.data.balance[self.data.market[sellId].seller] += sp.amount - self.data.sellfee

            # remove from market
            if not self.data.balance.contains(self.data.owner):
                self.data.balance[self.data.owner] = self.data.sellfee
            else:
                self.data.balance[self.data.owner] += self.data.sellfee
            del self.data.market[sellId]
            
        @sp.entrypoint
        def get_balance(self):
            assert self.data.users.contains(sp.sender), "You need to JoinTCg Before"
            assert self.data.balance.contains(sp.sender), "You have nothing to get"
            sp.send(sp.sender, self.data.balance[sp.sender])
            del self.data.balance[sp.sender]
            
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
        def buyCard(self, sellId):
            tcgcontract = sp.contract(buyCard_type, self.data.TCGContract, entrypoint="buyCard").unwrap_some()
            data = sp.record(userAddress = sp.sender, sellId = sellId)
            sp.transfer(data, sp.amount, tcgcontract)

        @sp.entrypoint
        def sellCard(self, id, price):
            tcgcontract = sp.contract(sellCard_type, self.data.TCGContract, entrypoint="sellCard").unwrap_some()
            data = sp.record(userAddress = sp.sender, cardId = id, price = price)
            sp.transfer(data, sp.tez(0), tcgcontract)

        @sp.entrypoint
        def askTrade(self, userAddress, askedCardId, givenCardId):
            tcgcontract = sp.contract(exchangeCard_type, self.data.TCGContract, entrypoint="exchangeCard").unwrap_some()
            data = sp.record(userAddress1 = sp.sender, userAddress2 = userAddress, cardId1 = givenCardId, cardId2 = askedCardId)
            sp.transfer(data, sp.tez(0), tcgcontract)
        
        @sp.entrypoint
        def processExchange(self, tradeId):
            tcgcontract = sp.contract(processExchange_type, self.data.TCGContract, entrypoint="processExchange").unwrap_some()
            sp.transfer(tradeId, sp.tez(0), tcgcontract)

        @sp.entrypoint
        def acceptTrade(self, tradeId):
            tcgcontract = sp.contract(acceptTrade_type, self.data.TCGContract, entrypoint="acceptTrade").unwrap_some()
            data = sp.record(tradeId = tradeId, userAddress = sp.sender)
            sp.transfer(data, sp.tez(0), tcgcontract)

        @sp.entrypoint
        def declineTrade(self, tradeId):
            tcgcontract = sp.contract(declineTrade_type, self.data.TCGContract, entrypoint="declineTrade").unwrap_some()
            data = sp.record(tradeId = tradeId, userAddress = sp.sender)
            sp.transfer(data, sp.tez(0), tcgcontract)
            

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
    c1.add_address_contract_User(c2.address, _sender=alice)
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
def test_sell_buy():
    scenario = sp.test_scenario("TezCG", main)
    alice = sp.test_account("alice").address
    bob = sp.test_account("bob").address
    random = sp.test_account("random").address
    
    scenario.h1("Test Sell and Buy Logic")
    c3 = main.OracleRandom(alice)
    c1 = main.TCGContract(alice,c3.address)
    c2 = main.UserContract(c1.address)
    
    scenario += c1
    scenario += c2
    scenario += c3

    c1.add_address_contract_User(c2.address, _sender=alice)
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

    c2.joinTCG("test",_sender=alice,_amount=sp.tez(1),_now=sp.timestamp_from_utc(2025,1,16,15,38,0))

    # Test for selling / buying card
    scenario.h2("Unit test: sellCard good")
    c2.sellCard(id = 1, price = sp.tez(10), _sender = bob, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 39, 0))
    scenario.verify(c1.data.market.contains(0))
    scenario.verify(c1.data.market[0].seller == bob)
    scenario.verify(c1.data.market[0].price == sp.tez(10))
    scenario.verify(c1.data.market[0].cardId == 1)

    scenario.h2("Unit test: buyCard good")
    c2.buyCard(0, _sender = alice, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 39, 0), _amount = sp.tez(12))
    scenario.verify(c1.data.users[alice].cards.contains(1))
    scenario.verify(c1.data.users[bob].cards.contains(1) == False)
    scenario.verify(c1.data.balance[bob] == sp.tez(10))
    scenario.verify(c1.data.balance[alice] == sp.tez(2))
    scenario.verify(c1.data.market.contains(0) == False)

    scenario.h2("Unit test: sellCard without owning the card (Error)")
    c2.sellCard(id = 2, price = sp.tez(10), _sender = bob, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 40, 0), _valid=False, _exception="You don't have this card")

    scenario.h2("Unit test: buyCard with incorrect amount (Error)")
    c2.sellCard(id = 1, price = sp.tez(10), _sender = alice, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 41, 0))
    c2.buyCard(1, _sender = bob, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 42, 0), _amount = sp.tez(11), _valid=False, _exception="You must send the exact amount")

    scenario.h2("Unit test: buyCard for non-existent sellId (Error)")
    c2.buyCard(99, _sender = bob, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 43, 0), _amount = sp.tez(12), _valid=False, _exception="This card is not on the market")

    scenario.h2("Unit test: buyCard without joining the game (Error)")
    c2.buyCard(1, _sender = random, _now = sp.timestamp_from_utc(2025, 1, 17, 15, 44, 0), _amount = sp.tez(12), _valid=False, _exception="You must join the game before")

#Test for trades
@sp.add_test()
def test_trades():
    scenario = sp.test_scenario("TezCG", main)
    alice = sp.test_account("alice").address
    bob = sp.test_account("bob").address
    random = sp.test_account("random").address
    john = sp.test_account("john").address
    
    scenario.h1("Test Trades")
    c3 = main.OracleRandom(alice)
    c1 = main.TCGContract(alice,c3.address)
    c2 = main.UserContract(c1.address)
    
    scenario += c1
    scenario += c2
    scenario += c3

    c1.add_address_contract_User(c2.address, _sender=alice)
    c2.joinTCG("bob_pseudo",_sender=bob,_amount=sp.tez(1),_now=sp.timestamp_from_utc(2025,1,16,15,38,0))
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

    c2.joinTCG("alice_pseudo",_sender=alice,_amount=sp.tez(1),_now=sp.timestamp_from_utc(2025,1,16,15,38,0))
    c2.getFreeBooster(_sender=alice,_now=sp.timestamp_from_utc(2025,1,17,15,39,0))
    
    
    scenario.h2("Unit test : askTrade good")
    tradeId = 0
    c2.askTrade(userAddress = alice, askedCardId = 2, givenCardId = 1, _sender=bob,_now=sp.timestamp_from_utc(2025,1,17,15,42,0))
    scenario.verify(c1.data.tradeId == tradeId + 1)
    scenario.verify(c1.data.trades.contains(tradeId))
    scenario.verify(c1.data.trades[tradeId].userAddress1 == bob)
    scenario.verify(c1.data.trades[tradeId].userAddress2 == alice)
    scenario.verify(c1.data.trades[tradeId].cardId1 == 1)
    scenario.verify(c1.data.trades[tradeId].cardId2 == 2)
    scenario.verify(c1.data.trades[tradeId].timer == sp.timestamp_from_utc(2025,1,17,15,42,0))
    scenario.verify(c1.data.trades[tradeId].accepted == False)
    
    scenario.h2("Unit test : acceptTrade good")
    c2.acceptTrade(tradeId, _sender=alice, _now=sp.timestamp_from_utc(2025,1,17,15,50,0))
    scenario.verify(c1.data.trades[tradeId].accepted == True)
    
    scenario.h2("Unit test : processExchange good")
    c2.processExchange(tradeId, _sender=random, _now=sp.timestamp_from_utc(2025,1,17,15,52,0))
    scenario.verify(c1.data.users[bob].cards.contains(2))
    scenario.verify(c1.data.users[alice].cards.contains(1))
    scenario.verify(c1.data.users[bob].cards.contains(1) == False)
    scenario.verify(c1.data.users[alice].cards.contains(2) == False)
    
    scenario.h2("Unit test : declineTrade good")
    tradeId = 1
    c2.askTrade(userAddress = alice, askedCardId = 1, givenCardId = 2, _sender=bob,_now=sp.timestamp_from_utc(2025,1,18,15,42,0))
    c2.declineTrade(tradeId, _sender=alice, _now=sp.timestamp_from_utc(2025,1,18,15,50,0))
    scenario.verify(c1.data.trades.contains(tradeId) == False)
    
    scenario.h2("Unit test : processExchange with refused trade")
    c2.processExchange(tradeId, _sender=random, _now=sp.timestamp_from_utc(2025,1,18,15,52,0), _valid=False, _exception="This trade does not exist or has been refused")
    scenario.h2("Unit test : processExchange with trade that does not exist")
    c2.processExchange(4, _sender=random, _now=sp.timestamp_from_utc(2025,1,18,15,53,0), _valid=False, _exception="This trade does not exist or has been refused")
    scenario.h2("Unit test : processExchange directly to TCGContract entrypoints")
    tradeId = 2
    c2.askTrade(userAddress = alice, askedCardId = 1, givenCardId = 2, _sender=bob,_now=sp.timestamp_from_utc(2025,1,19,15,42,0))
    c2.acceptTrade(tradeId, _sender=alice, _now=sp.timestamp_from_utc(2025,1,19,15,50,0))
    c1.processExchange(tradeId, _sender=random, _now=sp.timestamp_from_utc(2025,1,19,15,53,0), _valid=False, _exception="Only User_contract can interact with this endpoint")
    scenario.h2("Unit test : processExchange with trade not accepted yet")
    tradeId = 3
    c2.askTrade(userAddress = alice, askedCardId = 1, givenCardId = 2, _sender=bob,_now=sp.timestamp_from_utc(2025,1,20,15,42,0))
    c2.processExchange(tradeId, _sender=random, _now=sp.timestamp_from_utc(2025,1,20,15,53,0), _valid=False, _exception="Your trade partner does not have accepted yet")
    scenario.h2("Unit test : processExchange with trade when the player1 does not have the card")
    tradeId = 4
    c2.askTrade(userAddress = alice, askedCardId = 1, givenCardId = 2, _sender=bob,_now=sp.timestamp_from_utc(2025,1,21,15,42,0))
    c2.askTrade(userAddress = alice, askedCardId = 7, givenCardId = 2, _sender=bob,_now=sp.timestamp_from_utc(2025,1,21,15,45,0))
    c2.acceptTrade(tradeId + 1, _sender=alice, _now=sp.timestamp_from_utc(2025,1,21,15,50,0))
    c2.processExchange(tradeId + 1, _sender=random, _now=sp.timestamp_from_utc(2025,1,21,15,53,0))
    c2.acceptTrade(tradeId, _sender=alice, _now=sp.timestamp_from_utc(2025,1,21,15,54,0))
    c2.processExchange(tradeId, _sender=random, _now=sp.timestamp_from_utc(2025,1,21,15,55,0), _valid=False, _exception="You need to have the card that you want to trade")

    scenario.h2("Unit test : processExchange with trade when the player2 does not have the card")
    tradeId = 6
    c2.askTrade(userAddress = alice, askedCardId = 1, givenCardId = 5, _sender=bob,_now=sp.timestamp_from_utc(2025,1,22,15,42,0))
    c2.askTrade(userAddress = alice, askedCardId = 1, givenCardId = 8, _sender=bob,_now=sp.timestamp_from_utc(2025,1,22,15,45,0))
    c2.acceptTrade(tradeId + 1, _sender=alice, _now=sp.timestamp_from_utc(2025,1,22,15,50,0))
    c2.processExchange(tradeId + 1, _sender=random, _now=sp.timestamp_from_utc(2025,1,22,15,53,0))
    c2.acceptTrade(tradeId, _sender=alice, _now=sp.timestamp_from_utc(2025,1,22,15,54,0))
    c2.processExchange(tradeId, _sender=random, _now=sp.timestamp_from_utc(2025,1,22,15,55,0), _valid=False, _exception="Your trade partner need to have the card that you want to have from him")

    
    tradeId = 8
    scenario.h2("Unit test : askTrade directly to TCGContract entrypoints")
    c1.exchangeCard(userAddress1 = bob, userAddress2 = alice, cardId1 = 8, cardId2 = 1, _sender=bob,_now=sp.timestamp_from_utc(2025,1,23,15,42,0), _valid=False, _exception="Only User_contract can interact with this endpoint")
    scenario.verify(c1.data.trades.contains(tradeId) == False)
    scenario.h2("Unit test : askTrade with sender not in TCG")
    c2.askTrade(userAddress = alice, askedCardId = 8, givenCardId = 1, _sender=john,_now=sp.timestamp_from_utc(2025,1,23,15,46,0), _valid=False, _exception="You need to JoinTCg Before")
    scenario.verify(c1.data.trades.contains(tradeId) == False)
    scenario.h2("Unit test : askTrade with receiver not in TCG")
    c2.askTrade(userAddress = john, askedCardId = 8, givenCardId = 1, _sender=bob,_now=sp.timestamp_from_utc(2025,1,23,15,47,0), _valid=False, _exception="Your trade partner need to JoinTCg Before")
    scenario.verify(c1.data.trades.contains(tradeId) == False)
    scenario.h2("Unit test : askTrade with sender does not have the card")
    c2.askTrade(userAddress = alice, askedCardId = 8, givenCardId = 6, _sender=bob,_now=sp.timestamp_from_utc(2025,1,23,15,48,0), _valid=False, _exception="You need to have the card that you want to trade")
    scenario.verify(c1.data.trades.contains(tradeId) == False)
    scenario.h2("Unit test : askTrade with receiver does not have the card")
    c2.askTrade(userAddress = alice, askedCardId = 6, givenCardId = 1, _sender=bob,_now=sp.timestamp_from_utc(2025,1,23,15,49,0), _valid=False, _exception="Your trade partner need to have the card that you want to have from him")
    scenario.verify(c1.data.trades.contains(tradeId) == False)
    
    scenario.h2("Unit test : acceptTrade but tradeId does not exist")
    c2.acceptTrade(1, _sender=alice, _now=sp.timestamp_from_utc(2025,1,24,15,50,0), _valid=False, _exception="This trade does no longer exist")
    scenario.h2("Unit test : acceptTrade directly to TCGContract entrypoints")
    c1.acceptTrade(tradeId=3, userAddress=alice, _sender=alice, _now=sp.timestamp_from_utc(2025,1,20,15,45,0), _valid=False, _exception="Only User_contract can interact with this endpoint")
    scenario.verify(c1.data.trades[3].accepted == False)
    scenario.h2("Unit test : acceptTrade with sender not allowed to call entrypoint of this tradeId")
    c2.acceptTrade(3, _sender=bob, _now=sp.timestamp_from_utc(2025,1,20,15,46,0), _valid=False, _exception="You are not allowed to accept this trade")
    scenario.verify(c1.data.trades[3].accepted == False)
    scenario.h2("Unit test : acceptTrade with time limit expired")
    c2.acceptTrade(3, _sender=alice, _now=sp.timestamp_from_utc(2025,1,25,15,55,0), _valid=False, _exception="The time limit for this trade has expired => the trade is cancelled")

    
    
    c2.askTrade(userAddress = alice, askedCardId = 8, givenCardId = 1, _sender=bob,_now=sp.timestamp_from_utc(2025,1,26,15,46,0))
    scenario.h2("Unit test : declineTrade but tradeId does not exist")
    c2.declineTrade(1, _sender=alice, _now=sp.timestamp_from_utc(2025,1,26,15,50,0), _valid=False, _exception="This trade does no longer exist")
    scenario.h2("Unit test : declineTrade directly to TCGContract entrypoints")
    c1.declineTrade(tradeId=tradeId, userAddress=alice, _sender=alice, _now=sp.timestamp_from_utc(2025,1,26,15,48,0), _valid=False, _exception="Only User_contract can interact with this endpoint")
    scenario.verify(c1.data.trades.contains(tradeId))
    scenario.h2("Unit test : declineTrade with sender not allowed to call entrypoint of this tradeId")
    c2.declineTrade(tradeId, _sender=bob, _now=sp.timestamp_from_utc(2025,1,26,15,50,0), _valid=False, _exception="You are not allowed to decline this trade")
    scenario.verify(c1.data.trades.contains(tradeId))
    scenario.h2("Unit test : declineTrade with time limit expired")
    c2.declineTrade(tradeId, _sender=alice, _now=sp.timestamp_from_utc(2025,1,27,15,55,0), _valid=False, _exception="The time limit for this trade has expired => the trade is cancelled")
    scenario.verify(c1.data.trades.contains(tradeId) == False)