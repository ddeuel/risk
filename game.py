import random, pygame, sys, const, random
from pygame.locals import *

def main():
	choosy_agent(const.PLAYERS[1])

def random_agent(player):
	unclaimed_territories = []
	for territory in const.TERRITORIES:
		if territory["color"] == const.GRAY:
			unclaimed_territories.append(territory)
	if (unclaimedTerritory()):
		claim_territory(random.choice(unclaimed_territories), player)

	elif (const.fortifying_round < 7):
		friendlies = all_friendly_territories(player)
		place(random.choice(friendlies), player)

	elif (const.ACTIVITY == const.PLACE):
		if (player["troops_to_place"] > 0):
			friendlies = all_friendly_territories(player)
			place(random.choice(friendlies), player)
		else:
			const.ACTIVITY = const.ATTACK

	elif (const.ACTIVITY == const.ATTACK):
		can_attack = territories_available_to_attack(player)
		attack_times = random.randint(0, len(can_attack))
		while (len(can_attack) > 0 and attack_times > 0):
			can_attack = territories_available_to_attack(player)
			if (len(can_attack) > 0):
				attacking = random.choice(can_attack)
				can_defend = specific_enemy_neighbors(attacking)
				if (len(can_defend) > 0):
					defending = random.choice(can_defend)
					attack(attacking, defending, player)
					attack_times -= 1
		const.ACTIVITY = const.FORT

	elif (const.ACTIVITY == const.FORT):
		can_fortify = territories_available_to_fortify(player)
		fortify_times = random.randint(0, len(can_fortify))
		while (len(can_fortify) > 0 and fortify_times > 0):
			can_fortify = territories_available_to_fortify(player)
			if (len(can_fortify) > 0):
				origin = random.choice(can_fortify)
				add_to_fortify_queue(origin, player)
				can_receive = specific_friendly_neighbors(origin)
				if (len(can_receive) > 0):
					destination = random.choice(can_receive)
					place_from_fortify_queue(origin, destination, player)
					fortify_times -= 1
		const.ACTIVITY = const.PLACE
		if (const.current_player == len(const.PLAYERS)):
			const.current_player = 1
		else:
			const.current_player += 1
			for p in const.PLAYERS:
				reinforce_player(p)

def choosy_agent(player):
	unclaimed_territories = []
	for territory in const.TERRITORIES:
		if territory["color"] == const.GRAY:
			unclaimed_territories.append(territory)
	if (unclaimedTerritory()):
		best_territory = None
		best = -1000
		for territory in unclaimed_territories:
			enemy_territories = enemy_territories_in_continent(player, territory)
			friendly_territories = friendly_territories_in_continent(player, territory)

			current = friendly_territories - enemy_territories
			if current > best:
				best = current
				best_territory = territory

		claim_territory(best_territory, player)

	elif (const.fortifying_round < 7):
		friendlies = all_friendly_territories(player)
		neighboring_enemies = total_enemy_neighbors(friendlies)
		border_friendlies = total_enemy_neighbors(neighboring_enemies)
		greatest_enemy_threat = 0
		territories_to_fortify = []

		for border_friendly in border_friendlies:
			neighboring_enemy_troops = 0
			friendly_troops = border_friendly["troops"]

			for enemy_neighbor in specific_enemy_neighbors(border_friendly):
				neighboring_enemy_troops += enemy_neighbor["troops"]

			if (neighboring_enemy_troops - friendly_troops > greatest_enemy_threat):
				greatest_enemy_threat = neighboring_enemy_troops - friendly_troops
				territories_to_fortify = [border_friendly]

			elif (neighboring_enemy_troops - friendly_troops == greatest_enemy_threat):
				territories_to_fortify.append(border_friendly)
		place(random.choice(territories_to_fortify), player)

	elif (const.ACTIVITY == const.PLACE):
		if (player["troops_to_place"] > 0):
			friendlies = all_friendly_territories(player)
			neighboring_enemies = total_enemy_neighbors(friendlies)
			border_friendlies = total_enemy_neighbors(neighboring_enemies)
			greatest_enemy_threat = 0
			territories_to_fortify = []

			for border_friendly in border_friendlies:
				neighboring_enemy_troops = 0
				friendly_troops = border_friendly["troops"]

				for enemy_neighbor in specific_enemy_neighbors(border_friendly):
					neighboring_enemy_troops += enemy_neighbor["troops"]

				if (neighboring_enemy_troops - friendly_troops > greatest_enemy_threat):
					greatest_enemy_threat = neighboring_enemy_troops - friendly_troops
					territories_to_fortify = [border_friendly]

				elif (neighboring_enemy_troops - friendly_troops == greatest_enemy_threat):
					territories_to_fortify.append(border_friendly)
			if (len(territories_to_fortify) > 0):
				place(random.choice(territories_to_fortify), player)
		else:
			const.ACTIVITY = const.ATTACK

	elif (const.ACTIVITY == const.ATTACK):
		(attacking, defending) = decide_attack(player)
		attack(attacking, defending, player)
		const.ACTIVITY = const.FORT

	elif (const.ACTIVITY == const.FORT):
		const.ACTIVITY = const.PLACE
		if (const.current_player == len(const.PLAYERS)):
			const.current_player = 1
		else:
			const.current_player += 1
			for p in const.PLAYERS:
				reinforce_player(p)

def max_troop_attacker(enemy_territory):
	friendly_attackers = specific_enemy_neighbors(enemy_territory)
	friendly_troops = [specific_troop_strength(x) for x in friendly_attackers]
	max_friendly_troops = max(friendly_troops)
	most_troops_territory = friendly_attackers[friendly_troops.index(max_friendly_troops)]

	return (most_troops_territory, max_friendly_troops)

def decide_attack(player):
	friendlies = all_friendly_territories(player)
	friendlies_with_troops = territories_available_to_attack(player)

	attackable_enemy_territories = total_enemy_neighbors(friendlies_with_troops)

	attack_scores = []

	for enemy_territory in attackable_enemy_territories:

		enemy_troops = specific_troop_strength(enemy_territory)
		most_friendly_troops = max_troop_attacker(enemy_territory)[1]
		troop_difference = most_friendly_troops - enemy_troops

		for continent in const.CONTINENTS:
			if enemy_territory in continent["territories"]:
				enemy_continent = continent

		enemies_in_continent = enemy_territories_in_continent(player, enemy_continent)
		territories_in_continent = len(enemy_continent["territories"])
		friendlies_in_continent = territories_in_continent - enemies_in_continent

		attack_score = troop_difference + (friendlies_in_continent/territories_in_continent) * enemy_continent["bonus"]
		attack_scores.append(attack_score)

	best_attack_index = attack_scores.index(max(attack_scores))
	defending = attackable_enemy_territories[best_attack_index]

	attacking = max_troop_attacker(defending)[0]

	return attacking, defending


def territories_available_to_attack(player):
	can_attack = []
	for territory in const.TERRITORIES:
		if (territory["color"] == player["color"] and territory["troops"] > 1):
			can_attack.append(territory)
	return can_attack

def territories_available_to_fortify(player):
	can_fortify = []
	for territory in const.TERRITORIES:
		if (territory["color"] == player["color"] and territory["troops"] > 1):
			can_fortify.append(territory)
	return can_fortify


def all_friendly_territories(player):
	friendly_territories = []

	for t in const.TERRITORIES:
		if t["color"] == player["color"]:
			friendly_territories.append(t)

	return friendly_territories


def specific_friendly_neighbors(territory):
	color = territory["color"]

	for neighbor in const.NEIGHBORS:
		if neighbor["territory"] == territory:
			neighbors = neighbor["neighbors"]

	friendly_territories = []

	for n in neighbors:
		if n["color"] == color:
		  friendly_territories.append(n)

	return friendly_territories


def specific_enemy_neighbors(territory):
	color = territory["color"]

	for neighbor in const.NEIGHBORS:
		if neighbor["territory"] == territory:
			neighbors = neighbor["neighbors"]

	enemy_territories = []

	for n in neighbors:
		if n["color"] != color:
		  enemy_territories.append(n)

	return enemy_territories


def total_enemy_neighbors(friendlies):
	enemy_neighbors = []

	for f in friendlies:
		enemies = specific_enemy_neighbors(f)
		for enemy in enemies:
			if enemy not in enemy_neighbors:
				enemy_neighbors.append(enemy)

	return enemy_neighbors


def specific_troop_strength(territory):
	return territory["troops"]

def total_troop_strength(player):
	territories = all_friendly_territories(player)
	troops = [specific_troop_strength(t) for t in territories]
	total_troops = sum(troops)

	return troops

def enemy_territories_in_continent(player, territory):
	continent = None

	for c in const.CONTINENTS:
		if territory in c["territories"]:
			continent = c

	color = None

	enemy_territories = 0
	if (continent):
		for t in continent["territories"]:
			if (t["color"] != player["color"]) and (t["color"]!= const.GRAY):
				enemy_territories += 1

	return enemy_territories

def friendly_territories_in_continent(player, territory):
	continent = None

	for c in const.CONTINENTS:
		if territory in c["territories"]:
			continent = c

	color = None

	friendly_territories = 0
	if (continent):
		for t in continent["territories"]:
			if (t["color"] == player["color"]) and (t["color"]!= const.GRAY):
				friendly_territories += 1

	return friendly_territories

# returns true if there are unclaimed (gray) territories
def unclaimedTerritory():
  for territory in const.TERRITORIES:
    if (territory["color"] == const.GRAY):
      return True
  return False

def claim_territory(territory, player):
	if (territory["color"] == const.GRAY):
		territory["troops"] += 1
		territory["color"] = player["color"]
		player["troops_to_place"] -= 1


# place one troop in given destination territory
def place(destination, player):
	if (destination["color"] == player["color"]):
		destination["troops"] += 1
		player["troops_to_place"] -= 1

# maximum number of die will always be rolled for attacker and defender
# battle probabilites are hard coded using values obtained by simulation
# for speedy battles

# NEEDS TO BE IMPLEMENTED: CHOOSING HOW MANY TROOPS TO MOVE AFTER WINNING

def attack(attacking, defending, player):
	if (attacking in all_friendly_territories(player)) and (defending in specific_enemy_neighbors(attacking)):
		p = random.random()
		# rolling 3 die
		if (attacking["troops"] > 3):
			if (defending["troops"] > 1):
				if (p < .372):
					defending["troops"] -= 2
				if (p > .708):
					attacking["troops"] -= 2
				else:
					attacking["troops"] -= 1
					defending["troops"] -= 1
			if (defending["troops"] == 1):
				if (p < .66):
					defending["troops"] -= 1
				else:
					attacking["troops"] -= 1
		# rolling 2 die
		if (attacking["troops"] == 3):
			if (defending["troops"] > 1):
				if (p < .228):
					defending["troops"] -= 2
				if (p > .552):
					attacking["troops"] -= 2
				else:
					attacking["troops"] -= 1
					defending["troops"] -= 1
			if (defending["troops"] == 1):
				if (p < .579):
					defending["troops"] -= 1
				else:
					attacking["troops"] -= 1
		# rolling 1 die
		if (attacking["troops"] == 2):
			if (defending["troops"] > 1):
				if (p < .255):
					defending["troops"] -= 1
				else:
					attacking["troops"] -= 1
			if (defending["troops"] == 1):
				if (p < .417):
					defending["troops"] -= 1
				else:
					attacking["troops"] -= 1
		if (defending["troops"] < 1):
			defending["troops"] = (attacking["troops"] - 1)
			attacking["troops"] = 1
			defending["color"] = attacking["color"]

def add_to_fortify_queue(origin, player):
	if (origin["color"] == player["color"]):
		player["troops_to_place"] += (origin["troops"] - 1)
		origin["troops"] = 1

def place_from_fortify_queue(origin, destination, player):
	 if (destination in specific_friendly_neighbors(origin) or destination == origin):
		 destination["troops"] += 1
		 player["troops_to_place"] -= 1

def reinforce_player(player):
	player["troops_to_place"] = 3

	friendlies = all_friendly_territories(player)

	player["troops_to_place"] += int(len(friendlies)/3)

	player_territories = friendlies

	NORTH_AMERICA_owned = EUROPE_owned = SOUTH_AMERICA_owned = AFRICA_owned = ASIA_owned = OCEANIA_owned = False


	for territory in player_territories:
		if enemy_territories_in_continent(player, territory) == 0:

			if territory in const.NORTH_AMERICA["territories"] and NORTH_AMERICA_owned == False:
				player["troops_to_place"] += const.NORTH_AMERICA["bonus"]
				NORTH_AMERICA_owned = True

			if territory in const.EUROPE["territories"] and EUROPE_owned == False:
				player["troops_to_place"] += const.EUROPE["bonus"]
				EUROPE_owned = True

			if territory in const.SOUTH_AMERICA["territories"] and SOUTH_AMERICA_owned == False:
				player["troops_to_place"] += const.SOUTH_AMERICA["bonus"]
				SOUTH_AMERICA_owned = True

			if territory in const.AFRICA["territories"] and AFRICA_owned == False:
				player["troops_to_place"] += const.AFRICA["bonus"]
				AFRICA_owned = True

			if territory in const.ASIA["territories"] and ASIA_owned == False:
				player["troops_to_place"] += const.ASIA["bonus"]
				ASIA_owned = True

			if territory in const.OCEANIA["territories"] and OCEANIA_owned == False:
				player["troops_to_place"] += const.OCEANIA["bonus"]
				OCEANIA_owned = True

# press x to use this function in GUI, assigns all territories for testing purposes
def assign_territories():
	for i in range(len(const.TERRITORIES)):
		if (i % 2 == 0):
			const.TERRITORIES[i]["color"] = const.BLUE
		else:
			const.TERRITORIES[i]["color"] = const.RED
		const.TERRITORIES[i]["troops"] = 1

if __name__ == '__main__':
    main()
