from pprint import pprint
import time
from datetime import datetime
import pytz
import discord
from discord.ext import commands
import random
import os
import requests
import numpy as np
from bs4 import BeautifulSoup
import json
import asyncio
import re

client=commands.Bot(command_prefix="!")
main_shop=[{"name":"Watch","price":100,"description":"to tell time"},
		{"name":"Laptop","price":1000,"description":"for doing work"},
		{"name":"PC","price":10000,"description":"for gaming"}]
evan_schedule={# norm/early/hr_early/2hr_delay
	"06:28/06:28":"Hurry up!",
	"07:16/no":"E23",
	"07:38/07:16":"B110",
	"08:28/07:59":"H3",
	"09:17/08:35":"K130",
	"10:06/09:11":"A8",
	"10:55/09:47":"E110",
	"11:43/10:23":{"A":"F125","B":"FOOD","C":"GYM","D":"F125","E":"FOOD","F":"GYM"},
	"12:30/10:59":{"A":"FOOD","B":"CAFE","C":"FOOD","D":"FOOD","E":"K231","F":"FOOD"},
	"13:19/11:35":"K231",
	"14:10/12:10":"Pack up"}
schedule_dict={
	"toomeem#0389":evan_schedule
}
school_times={
	"norm":["07:21","14:12"],
	"early":["07:21","11:00"],
}
no_eat=["milk", "fruit cup", "pasta", "sausage", "macaroni", "cheese", "salad", "pretzel", "spanish beans", "muffin", "max sticks", "bosco", "broccoli", "nacho", "vegetable", "juice", "mozzarella", "roll", "buffalo", "spartan", "sweet and sour", "parm", "sausage", "knights", "100%", "chicken bowl", "carrot", "celery", "pizza"]
months=["january","february","march","april","may","june","july","august","september","october","november","december"]
have_crypto=lambda:True

def rn(target="%H:%M"):
	now=datetime.now(pytz.timezone("America/New_York"))
	return now.strftime(target)

@client.event
async def on_ready():
	await client.wait_until_ready()
	print("Connected")
	daily_funcs()
	#channel=client.get_channel(801836482960556133)

@client.event
async def on_command_error(ctx,error):
	if "CommandNotFound" in str(error):
		await ctx.send("That command does not exist. To see a list of all commands,send !commands")

@client.event
async def on_member_join(member):
	channel=client.get_channel(801836482960556133)
	channel.send(f"Welcome {member.name()}")
	channel.send("To learn more about me, send !info")

@client.event
async def on_member_remove(member):
	channel=client.get_channel(801836482960556133)
	channel.send(f"Bye {member.name()} ;(")

@client.command(aliases=["kill","terminate"])
async def end(message):
	if log_command("kill"):
		return
	await client.close()

@client.command(aliases=["bal"])
async def balance(ctx):
	if log_command("balance"):
		return
	user=ctx.author
	await open_account(ctx.author)
	users=await get_bank_data()
	wallet_amt=users[str(user.id)]["wallet"]
	bank_amt=users[str(user.id)]["bank"]
	em=discord.Embed(title=f"{ctx.author.name}'s balance",color=discord.Color.red())
	em.add_field(name="wallet balance",value=wallet_amt)
	em.add_field(name="bank balance",value=bank_amt)
	await ctx.send(content=":money_mouth:",embed=em)

@client.command()
async def beg(ctx):
	if log_command("beg"):
		return
	user=ctx.author
	await open_account(user)
	bal=await update_bank(ctx.author)
	if bal[0]+bal[1]>50:
		await ctx.send("You have enough money to get by.")
		return
	users=await get_bank_data()
	earnings=random.randrange(101)
	await ctx.send(f"Someone gave you {earnings} coins!")
	users[str(user.id)]["wallet"]+=earnings
	with open("text_files/main_bank.json","w") as f:
		json.dump(users,f)


@client.command(aliases=["wd"])
async def withdraw(ctx,amount=None):
	if log_command("withdraw"):
		return
	await open_account(ctx.author)
	bal=await update_bank(ctx.author)
	if amount==None:
		await ctx.send("Please enter the amount")
		return
	elif amount=="all":
		amount=bal[1]
	amount=int(amount)
	if amount>bal[1]:
		await ctx.send("You don't have that much money!")
		return
	elif amount<0:
		await ctx.send("Amount must be positive!")
		return
	await update_bank(ctx.author,amount)
	await update_bank(ctx.author,-1*amount,"bank")
	await ctx.send(f"You withdrew {amount} coins!")

@client.command(aliases=["dp"])
async def deposit(ctx,amount=None):
	if log_command("deposit"):
		return
	await open_account(ctx.author)
	bal=await update_bank(ctx.author)
	if amount==None:
		await ctx.send("Please enter the amount")
		return
	elif amount=="all":
		amount=bal[0]
	amount=int(amount)
	if amount>bal[0]:
		await ctx.send("You don't have that much money!")
		return
	elif amount<0:
		await ctx.send("Amount must be positive!")
		return
	await update_bank(ctx.author,-1*amount)
	await update_bank(ctx.author,amount,"bank")
	await ctx.send(f"You deposited {amount} coins!")

@client.command()
async def send(ctx,amount=None,*,arg:discord.Member):
	if log_command("send"):
		return
	await open_account(ctx.author)
	await open_account(arg)
	bal=await update_bank(ctx.author)
	if amount==None:
		await ctx.send("Please enter the amount")
		return
	if amount=="all":
		amount=bal[0]
	amount=int(amount)
	if amount>bal[0]:
		await ctx.send("You don't have that much money!")
		return
	elif amount<0:
		await ctx.send("Amount must be positive!")
		return
	await update_bank(ctx.author,-1*amount,"bank")
	await update_bank(arg,amount,"bank")
	await ctx.send(f"You gave {amount} coins!")

@client.command()
async def slots(ctx,amount=None):
	if log_command("slots"):
		return
	await open_account(ctx.author)
	bal=await update_bank(ctx.author)
	if amount==None:
		await ctx.send("Please enter the amount")
		return
	elif amount=="all":
		amount=bal[0]
	amount=int(amount)
	if amount>bal[0]:
		await ctx.send("You don't have that much money!")
		return
	elif amount<0:
		await ctx.send("Amount must be positive!")
		return
	em=discord.Embed(title="Slot Machine")
	final=""
	for i in range(3):
		a=random.choice(["X","O"])
		final+=a
	em.add_field(value=final)
	await ctx.send(content="$$$",embed=em)
	if final[0]==final[1] and final[0]==final[2] and final[1]==final[2]:
		await update_bank(ctx.author,3*amount)
		await ctx.send(f"You won {amount} coins!")
	else:
		await update_bank(ctx.author,-1*amount)
		await ctx.send(f"You lost {amount} coins!")

@client.command()
async def rob(ctx,*,arg:discord.Member):
	if log_command("rob"):
		return
	await open_account(ctx.author)
	await open_account(arg)
	bal=await update_bank(arg)
	if bal[0]<100:
		await ctx.send(f"{arg} doesn't have enough money!")
		return
	earnings=random.randrange(0,bal[0])
	await update_bank(ctx.author,earnings)
	await update_bank(arg,-1*earnings)
	await ctx.send(f"You stole {earnings} from {arg}")

@client.command()
async def shop(ctx):
	if log_command("shop"):
		return
	em=discord.Embed(title="Shop")
	for item in main_shop:
		name=item["name"]
		price=item["price"]
		desc=item["description"]
		em.add_field(name=name,value=f"${price} | {desc}")
	await ctx.send(content=":handshake:",embed=em)

@client.command()
async def buy(ctx,item,amount=1):
	if log_command("buy"):
		return
	await open_account(ctx.author)
	res=await buy_this(ctx.author,item,amount)
	if not res[0]:
		if res[1]==1:
			await ctx.send("That object isn't there!")
			return
		elif res[1]==2:
			await ctx.send("You don't have enough money in your wallet to buy this")
			return
	await ctx.send(f"You just bought {amount} {item}")

@client.command()
async def bag(ctx):
	if log_command("bag"):
		return
	await open_account(ctx.author)
	user=ctx.author
	users=await get_bank_data()
	try:
		bag=users[str(user.id)]["bag"]
	except:
		await ctx.send("You don't have any items")
		return
	em=discord.Embed(title="Your Bag")
	for item in bag:
		name=item["item"]
		amount=item["amount"]
		em.add_field(name=name,value=amount)
	await ctx.send(content=":face_with_monocle:",embed=em)

@client.command()
async def sell(ctx,item,amount=1):
	if log_command("sell"):
		return
	await open_account(ctx.author)
	res=await sell_this(ctx.author,item,amount)
	if not res[0]:
		if res[1]==1:
			await ctx.send("That object isn't there!")
			return
		elif res[1]==2:
			await ctx.send(f"You don't have {amount} {item} in your bag")
			return
	await ctx.send(f"You just sold {amount} {item}")

@client.command(aliases=["lb"])
async def leaderboard(ctx,x=3):
	if log_command("leaderboard"):
		return
	users=await get_bank_data()
	if x>len(users):
		x=1
	leader_board={}
	total=[users[user]["bank"]+users[user]["wallet"] for user in users]
	for user in users:
		leader_board[total]=int(user)
	total=sorted(total,reverse=True)
	em=discord.Embed(title=f"Top {x} richest members",color=discord.Color.red())
	index=1
	for amt in total:
		member=await client.fetch_user(leader_board[amt])
		name=member.name
		em.add_field(name=f"{index}. {name}",value=f"{amt}",inline=False)
		if index==x:
			break
		else:
			index+=1
	await ctx.send(content="Leaderboard",embed=em)

@client.command(aliases=["the earth king has invited you to lake laogai"])
async def the_earth_king_has_invited_you_to_lake_laogai(ctx):
	if log_command("lake laogai"):
		return
	await asyncio.sleep(1.5)
	await ctx.send("I am honoured to accept his invitation.")

@client.command()
async def alarm(ctx):
	if log_command("alarm"):
		return
	author=ctx.author
	with open("text_files/alarm") as alarm_file:
		alarm_dict={}
		for i in alarm_file.readlines():
			alarm_dict.update({i.split(" ")[0]:bool(int(i.split(" ")[1]))})
	if str(author) in alarm_dict:
		alarm_dict[str(author)]=False if alarm_dict[str(author)] else True
		with open("text_files/alarm","w") as alarm_file:
			for i in alarm_dict.keys():
				alarm_file.write(f"{i} {int(alarm_dict[i])}\n")
		alarm_state="on" if bool(alarm_dict[i]) else "off"
		await ctx.send(f"@{str(author)} your alarm is now {alarm_state}")
	else:
		await ctx.send(f"@{str(author)} you have not registered a schedule. If you would like to, please contact Evan.")

@client.command()
async def temp(ctx):
	if log_command("temp"):
		return
	temp=get_weather("temp")
	await ctx.send(f"{temp}°")

@client.command()
async def spam(ctx,*message):
	if log_command("spam"):
		return
	for i in range(5):
		if "str" in str(type(message)):
			await ctx.send(message)
		else:
			await ctx.send(" ".join(message))
		await asyncio.sleep(1)

@client.command(aliases=["war in ba sing se"])
async def war(ctx,*args):
	if log_command("war in ba sing se"):
		return
	if " ".join(args)!="in ba sing se":
		return
	for i in range(3):
		await asyncio.sleep(1)
		await ctx.send("There is no war within the walls.")
		await asyncio.sleep(1)
		await ctx.send("Here we are safe.")
		await asyncio.sleep(1)
		await ctx.send("Here we are free.")
		await asyncio.sleep(2)
	await asyncio.sleep(1)
	await ctx.send("Inside the walls we are safe.")

@client.command(aliases=["price"])
async def crypto(ctx,message):
	if log_command("crypto"):
		return
	price=crypto_price(message)
	if price!="error":
		await ctx.send(f"${price}")

@client.command()
async def profit(ctx):
	if log_command("profit"):
		return
	total_profit=get_profit()
	uni_price=crypto_price("uniswap")
	btc_price=crypto_price("bitcoin")
	if uni_price=="error" or btc_price=="error":
		error_report("profit")
		return "error"
	uni_profit=round((((uni_price-24.8)*2)/49.6)*100,2)
	btc_profit=round((((btc_price*.000717)-30)/30)*100,2)
	color=discord.Colour.red() if total_profit<0 else discord.Colour.green()
	em=discord.Embed(title="Crypto Profits",color=color)
	em.add_field(name="Uniswap profits",value=f"{uni_profit}%")
	em.add_field(name="Bitcoin profits",value=f"{btc_profit}%")
	em.add_field(name="Net gain",value=f"${total_profit}")
	if total_profit<0:
		await ctx.send(content=":clown:",embed=em)
	else:
		await ctx.send(content=":money_mouth:",embed=em)

@client.command()
async def weather(ctx):
	if log_command("weather"):
		return
	em=formatted_weather("Weather",discord.Color.light_grey())
	message=weather_emoji()
	await ctx.send(content=f":{message}:",embed=em)

@client.command()
async def battery(ctx):
	if log_command("battery"):
		return
	if not during_school():
		await asyncio.sleep(.5)
		await ctx.send("Hey stupid!")
		await asyncio.sleep(.5)
		await ctx.send("You aren't even in school.")
		return
	day=get_day_type()
	start=school_times[day][0]
	end=school_times[day][1]
	school_done=((int(rn("%H"))-int(start[:2]))*60)+(int(rn("%M"))-int(start[3:]))
	school_time=((int(end[:2])-int(start[:2]))*60)+(int(end[3:])-int(start[3:]))
	percent=10+int(83-(school_done/school_time*83))
	await ctx.send(f"{percent}%")

@client.command()
async def suggest(ctx, *args):
	if log_command("suggest"):
		return
	with open("text_files/suggestions","a") as suggestions:
		if "str" in str(type(suggestions)):
			suggestions.write(f"{args}\n")
		else:
			args=" ".join(args)
			suggestions.write(f"{args}\n")	
	await asyncio.sleep(3)
	await ctx.send("Sorry I am a slow reader.")
	await asyncio.sleep(2)
	await ctx.send("That looks like a good suggestion, I will pass it along.")
	await asyncio.sleep(1)
	await ctx.send("Thanks!")

@client.command()
async def quote(ctx):
	if log_command("quote"):
		return
	await ctx.send(get_quote())

@client.command()
async def school(ctx):
	if log_command("school"):
		return
	if int(rn("%y"))>=22:
		day_hours=162-int(rn("%j"))
	else:
		day_hours=365+162-int(rn("%j"))
	hours=int(rn("%H"))
	left=6840-(24*day_hours+hours)
	em=discord.Embed(title="Remaining School",footer="Work hard for college.")
	em.add_field(name="Percent of school completed",value=f"{str(np.round((left/6840)*100,1))}%")
	em.add_field(name="Days till school is over",value=str(np.round(285-left/24,1)))
	await ctx.send(content=":nerd:",embed=em)

@client.command(aliases=["coming soon"])
async def coming(ctx):
	if log_command("coming soon"):
		return
	with open("text_files/coming_soon") as coming_soon_file:
		coming_soon=coming_soon_file.readlines()
	if coming_soon!=[]:
		await ctx.send("Features on the way")
		for i in coming_soon:
			await ctx.send(i)
	else:
		await ctx.send("Nothing")			
@client.command()
async def scan(ctx,keyword):
	if log_command("scan"):
		return
	await ctx.send(content=":thinking:",embed=get_quote(True))

@client.command(aliases=["bdays"])
async def bday(ctx):
	if log_command("bday"):
		return
	bday_page=requests.get("https://www.brainyquote.com/")
	bday_soup=BeautifulSoup(bday_page.content,"html.parser").get_text()
	bdays=re.findall("- .+",bday_soup)[1:6]
	if len(bdays)!=5:
		error_report("bday")
		return
	em=discord.Embed(title="Famous People that were Born Today",color=discord.Color.orange())
	for i in bdays:
		em.add_field(value=i[2:])
	await ctx.send(content=":partying_face:",embed=em)

@client.command()
async def today(ctx):
	if log_command("today"):
		return
	day_num=int(rn("%d"))
	suffix=num_suffix(int(rn("%d")[1]))
	await ctx.send(rn(f"Today is %A, %b {day_num}{suffix}"))
	if during_school("day"):
		letr_day=letter_day()
		if letr_day!="error":
			if letr_day in "AEF":
				await ctx.send(f"It is an {letr_day} day")
			else:
				await ctx.send(f"It is a {letr_day} day")

@client.command()
async def info(ctx):
	if log_command("info"):
		return
	em=discord.Embed(title="I am Evan's personal bot.",color=discord.Color.purple(),footer="Have an amazing day!  ;)")
	em.add_field(value="If I am going crazy and you need to terminate me, send END")
	em.add_field(value="If you would like to see my commands, send !commands.")
	em.add_field(value="If you have any suggestions on new features that you would like added to me, send !suggest before your suggestion.")
	em.add_field(value="I will pass all suggestions along to my developer.")
	em.add_field(value="I hope you enjoy your time in Evan's server.")
	await ctx.send(content="Hello",embed=em)

@client.command()
async def commands(ctx):
	if log_command("commands"):
		return
	commands={
	"alarm":"toggles whether or not ping the sender when one of their classes ends"
	,"temp":"sends the current temperature where Evan lives"
	,"spam ___":"spams any message"
	,"war in ba sing se":"There is no war in Ba Sing Se. Here we are safe."
	,"crypto ___":"sends current price of of any popular crypto"
	,"profit":"sends the net profit from all  of Evan's crypto assets"
	,"weather":"sends a brief overview of the current weather conditions where Evan lives"
	,"battery":"sends the suggested amount of battery remaining on your phone to make it through the school day with 10% remaining"
	,"suggest ___":"reads and logs any suggestions"
	,"quote":"sends a random quote"
	,"school":"sends how much summer break is left"
	,"coming soon":"sends a list of features that will be added soon in order of importance"
	,"scan ___":"searches through all the unused quotes that contain that word/phrase"
	,"bday":"sends 5 famous people that were born today"
	,"today":"sends the day of the month, week, and school cycle"
	,"info":"sends my tinder bio"
	,"commands":"sends this"}
	await ctx.send("All commands MUST have an ! right before them")
	for key,val in commands.items():
		await ctx.send(key+" -> "+val)
		time.sleep(.5)
	await ctx.send("I also have a few other surprises ;)")

@client.command()
async def clean(ctx):
	if log_command("clean"):
		return
	daily_funcs()
	with open("text_files/quotes") as quotes_file:
		quotes=list(set(quotes_file.readlines()))
	with open("text_files/used_quotes") as used_quotes_file:
		used_quotes=list(set(used_quotes_file.readlines()))
	for i in quotes:
		if i in used_quotes:
			quotes.remove(i)
			used_quotes.append(i)
	quote_fix=False
	used_fix=False
	with open("text_files/quotes") as quotes_file:
		if quotes!=quotes_file.readlines():
			quote_fix=True
	with open("text_files/used_quotes") as used_quotes_file:
		if used_quotes!=used_quotes_file.readlines():
			used_fix=True
	if quote_fix:
		with open("text_files/quotes","w") as quotes_file:
			quotes_file.writelines(quotes)
	if used_fix:
		with open("text_files/used_quotes","w") as used_quotes_file:
			used_quotes_file.writelines(used_quotes)
	with open("text_files/alarm") as alarm_file:
		alarms=alarm_file.readlines()
	for i in alarms:
		try:
			i=int(i[-2])
		except:
			await ctx.send("error in alarm file")
			error_report("alarm_file")
	with open("text_files/special_days") as special_file:
		special_days=special_file.readlines()
	upcoming_days=[]
	for i in special_days:
		if int(i[3:5])>int(rn("%m")) or int(i[:2])>int(rn("%y")):
			upcoming_days.append(i)
			continue
		if int(i[3:5])==int(rn("%m")):
			if int(i[6:8])>=int(rn("%d")):
				upcoming_days.append(i)
	upcoming_days.sort()
	with open("text_files/special_days","w") as special_file:
		for i in(upcoming_days):
			special_file.write(i)
	with open("text_files/raw_lunches") as raw_lunches:
		lunches=list(raw_lunches.readlines())
	month=rn("%B").lower()
	month_index=len(lunches)
	for i in range(len(lunches)):
		if month in lunches[i].lower():
			month_index=i
			break
	print(month_index)
	lunches=lunches[month_index:]
	with open("text_files/raw_lunches","w") as raw_lunches:
		raw_lunches.writelines(lunches)
	await ctx.send("All Clean!")








async def sell_this(user,item_name,amount):
	in_shop=False
	price=None
	for item in main_shop:
		if item_name==item["name"]:
			in_shop=True
			price=item["price"]
			break
	if not in_shop:
		return [False,1]
	cost=price*amount
	users=await get_bank_data()
	try:
		index=0
		in_bag=False
		for bag_item in users[str(user.id)]["bag"]:
			thing=bag_item["item"]
			if thing==item_name:
				old_amt=bag_item["amount"]
				new_amt=old_amt-amount
				if new_amt<0:
					return [False,2]
				users[str(user.id)]["bag"][index]["amount"]=new_amt
				in_bag=True
				break
			index+=1
		if not in_bag:
			return [False,3]
	except:
		return[False,3]
	with open("text_files/main_bank.json","w") as f:
		json.dump(users,f)
	await update_bank(user,cost,"wallet")
	return [True]


async def buy_this(user,item_name,amount):
	in_shop=False
	price=None
	for item in main_shop:
		if item_name.lower()==item["name"].lower():
			in_shop=True
			price=item["price"]
			break
	if not in_shop:
		return [False,1]
	cost=price*amount
	users=await get_bank_data()
	bal=await update_bank(user)
	if bal[0]<cost:
		return [False,2]
	try:
		index=0
		in_bag=False
		for n in users[str(user.id)]["bag"]:
			thing=n["item"]
			if thing.lower()==item_name.lower():
				old_amt=n["amount"]
				new_amt=old_amt+amount
				users[str(user.id)]["bag"][index]["amount"]=new_amt
				in_bag=True
				break
			index+=1
		if not in_bag:
			obj={"item":item_name,"amount":amount}
			users[str(user.id)]["bag"].append(obj)
	except:
		obj={"item":item_name,"amount":amount}
		users[str(user.id)]["bag"]=[obj]
	with open("text_files/main_bank.json","w") as f:
		json.dump(users,f)
	await update_bank(user,cost*-1,"wallet")
	return [True]

async def open_account(user):
	users=await get_bank_data()
	with open("text_files/main_bank.json") as f:
		users=json.load(f)
	if str(user.id) in users:
		return False
	else:
		users[str(user.id)]={}
		users[str(user.id)]["wallet"]=0
		users[str(user.id)]["bank"]=0
	with open("text_files/main_bank.json","w") as f:
		json.dump(users,f)
	return True
def get_bank_data():
	with open("text_files/main_bank.json") as f:
		users=json.load(f)
	return users

async def update_bank(user,change=0,mode="wallet"):
	users=await get_bank_data()
	users[str(user.id)][mode]+=change
	with open("text_files/main_bank.json","w") as f:
		json.dump(users,f)
	bal=[users[str(user.id)]["wallet"],users[str(user.id)]["bank"]]
	return bal

def during_school(start="07:21",end="14:12"):	
	if rn("%a") in "SunSat":
		return False
	day_type=get_day_type()
	if day_type=="off": return False
	elif day_type=="early": end="12:12"
	elif day_type=="hrearly": end="13:12"
	elif day_type=="2hrdelay": start="09:21"
	if start=="day":
		return True
	try:
		start=int(start.split(":")[0])*60+int(start.split(":")[1])
		end=int(end.split(":")[0])*60+int(end.split(":")[1])-start
		now=int(rn("%H"))*60+int(rn("%H"))-start
	except:
		error_report("during_school")
		return
	return(0<=now<=end)

def crypto_price(name):
	try:
		crypto_page=requests.get(f"https://coinstats.app/coins/{name}/")
		crypto_soup=BeautifulSoup(crypto_page.content,"html.parser").get_text()
		search_string=name.capitalize()+" price is \$.+\d, "
		crypto_price=re.search(search_string,crypto_soup).group()[:-2].split("is $")[1]
		uncancel("crypto_price")
		if "," in crypto_price:
			crypto_price=crypto_price.replace(",","")
			crypto_price=float("".join(crypto_price))
			return(crypto_price)
		return(float(crypto_price))
	except:
		error_report("crypto_price")
		return "error"

def get_profit(worth=False):
	uni_price=crypto_price("uniswap")
	bit_price=crypto_price("bitcoin")
	if uni_price=="error" or bit_price=="error":
		error_report("profit")
		return "error"
	total=round((uni_price*2)+(bit_price*.000717)-(49.6+30),2)
	return total

def log_command(name):
	with open("text_files/command_list","a") as command_file:
		command_file.write(f"{name}\n")
	with open("text_files/cancel") as cancel_file:
		cancels=cancel_file.readlines()
	return(name in cancels)

def letter_day():
	try:
		letr_page=requests.get("https://nphs.npenn.org/our_school/nphs_information/daily_announcements")
		letr_soup=BeautifulSoup(letr_page.content,"html.parser").get_text()
		letr_day=re.search("[ABCDEF] Day",letr_soup).group()[0]
		if letr_day not in "ABCDEF":
			letr_day=1/0
		uncancel("letter_day")
	except:
		error_report("letter_day")
		return "error"
	return(letr_day)

def schedule(day_type,letr_day):
	if int(rn("%S"))>15 or not during_school("day"):
		return
	day_index=0
	if day_type=="early": day_index=1
	elif day_type=="hr_early": day_index=2
	elif day_type=="2hr_delay": day_index=3
	found_time=False
	with open("text_files/alarm") as alarm_file:
		alarms=alarm_file.readlines()
	alarm_dict={}
	for i in alarms:
		alarm_dict.update({i.split(" ")[0]:bool(int(i.split(" ")[1][:-1]))})
	for schedule in schedule_dict.items():
		if alarm_dict[schedule[0]]:
			schedule=schedule[1]
		else:
			continue
		for i in schedule.keys():
			target=i.split("/")[day_index]
			if target=="no":
				continue
			elif rn()==target:
				response=schedule[i]
				found_time=True
	if not found_time:
		return
	if type_checker(response,"str"):
		return response
	return send_cycle(response,letr_day)

def send_cycle(response,letr_day):
	if response[letr_day]!="FOOD":
		return response[letr_day]
	with open("text_files/lunches") as lunch_file:
		lunches=lunch_file.readlines()
	todays_lunch=[i for i in lunches]
	for i,food in enumerate(todays_lunch):
		food=food.lower()
		good,chicken_patty=False,True
		if food.startswith(rn("%b")):
			if rn("%d")==int(food.split(" ")[1]):
				good=True
			else:
				break
		for bad in no_eat:
			if bad not in food and good:
				todays_lunch[i]=food
				chicken_patty=False
	message=["Today you will be eating:"]
	if chicken_patty:
		message.append("Chicken Patty")
	else:
		for item in todays_lunch:
			message.append(f"\t{item.capitalize()}")	
	return message

def error_report(name):
	time_stamp=rn("%y/%m/%d/%H/%M/%S")
	with open("text_files/errors") as error_file:
		errors=error_file.readlines()
	if len(errors)>=40: errors=errors[30:]
	elif len(errors)>=10: errors=errors[10:]
	elif len(errors)>=5: errors=errors[5:]
	if len(errors)>5 and errors.count(errors[0])==len(errors):
		with open("text_files/cancel") as cancel_file:
			cancels=cancel_file.readlines()
		cancels.append(name+"\n")
		cancels=list(set(cancels))
		with open("text_files/cancel","w") as cancel_file:
			cancel_file.writelines(cancels)
	else:
		with open("text_files/errors","a") as error_list:
			error_list.write(f"{name}:{time_stamp}\n")

def get_weather(data="full"):
	weather_page=requests.get("https://forecast.weather.gov/MapClick.php?lat=40.2549&lon=-75.2429#.YXWhSOvMK02")
	weather_soup=BeautifulSoup(weather_page.content,"html.parser")
	if "Not a current observation" in str(weather_soup):
		error_report("weather")
		return "error"
	full=data=="full"
	if data=="conditions" or full:
		conditions=re.search("\">.+</p",str(weather_soup)).group()[2:-3]
	weather_soup=str(weather_soup.get_text())
	if data=="temp" or full:
		try:
			temp=int(re.search("Wind Chill*\d+°F",weather_soup).group()[10:-2])
		except:
			temp=int(np.round(float(re.search("\d+°F",weather_soup).group()[:-2]),0))
	if data=="humidity" or full:
		humidity=int(re.search("\d+%",weather_soup).group()[:-1])
	if data=="wind_speed" or full:
		wind_speed=int(re.search("\d+\smph",weather_soup).group()[:-4])
		if ("Calm" in weather_soup) and (" Calm" not in weather_soup):
			wind_speed=0
	if data=="dewpoint" or full:
		dewpoint=int(re.search("Dewpoint\s\d+°F",weather_soup).group()[9:-2])
	if data=="vis" or full:
		vis=re.search("Visibility\n.+",weather_soup).group().replace("Visibility\n","")
	if data=="conditions":
		return conditions
	elif data=="temp":
		return temp
	elif data=="humidity":
		return humidity
	elif data=="wind_speed":
		return wind_speed
	elif data=="dewpoint":
		return dewpoint
	elif data=="vis":
		return vis
	weather_data={"conditions":conditions,"temp":temp,"humidity":humidity,
								"wind_speed":wind_speed,"dewpoint":dewpoint,"vis":vis}
	return weather_data

def formatted_weather(title,color=False,footer=False):
	weather=get_weather()
	try:
		conditions,temp,humidity,wind_speed,dewpoint=weather["conditions"],weather["temp"],weather["humidity"],weather["wind_speed"],weather["dewpoint"]
	except:
		error_report("formatted_weather")
	if color:
		em=discord.Embed(title=title,colour=color)
	else:
		em=discord.Embed(title=title)
	em.add_field(name="Temperature",value=f"{temp}°")
	em.add_field(name="Conditions",value=conditions)
	if 62<dewpoint<69: em.add_field(name="Humidity",value="Above Average")
	elif 69<=dewpoint: em.add_field(name="Humidity",value="High")
	elif humidity<=30: em.add_field(name="Humidity",value="Very Low")
	elif humidity<=45: em.add_field(name="Humidity",value="Low")
	else: em.add_field(name="Humidity",value="Average")
	if wind_speed>=25: em.add_field(name="Wind Speed",value="Extremely high")
	elif 17<=wind_speed<25: em.add_field(name="Wind Speed",value="Very high")
	elif 10<=wind_speed<17: em.add_field(name="Wind Speed",value="Somewhat windy")
	elif 5<=wind_speed<10: em.add_field(name="Wind Speed",value="Light breeze")
	else: em.add_field(name="Wind Speed",value="Negligible")
	em.add_field(name="Visibility",value=weather["vis"])
	if footer:
		em.set_footer(text=footer)
	return em

def weather_emoji():
	weather=get_weather("conditions")
	message="face_in_clouds"
	if weather=="Partly Cloudy": message="white_sun_small_cloud"
	elif weather=="Sunny": message="sunny"
	elif weather=="Rain": message="cloud_rain"
	elif weather=="Sunny": message="sunny"
	elif weather=="Cloudy": message="white_sun_cloud"
	elif weather=="Isolated Showers": message="white_sun_rain_cloud"
	elif weather=="Partly Sunny": message="partly_sunny"
	elif weather=="Foggy": message="fog"
	elif weather=="Snow": message="cloud_snow"
	elif weather=="Overcast": message="cloud"
	elif weather=="Fair": message="white_sun_small_cloud"
	elif weather=="Thunderstorms": message="thunder_cloud_rain"
	return f":{message}:"

def crypto_profitable():
	now_profit=float(get_profit())
	if now_profit=="error" or not have_crypto():
		return "error"
	return now_profit>0

def uncancel(name):
	with open("text_files/cancel") as cancel_file:
		cancels=cancel_file.readlines()
	name+="\n"
	if name in cancels:
		cancels.remove(name)
	else:
		return
	with open("text_files/cancel","w") as cancel_file:
		cancel_file.writelines(cancels)

def get_quote(scan=False):
	with open("text_files/used_quotes") as used_quotes_file:
		used_quotes=(used_quotes_file.readlines())
	with open("text_files/quotes") as quotes_file:
		quote_list=list(set(quotes_file.readlines()))
	if "" in quote_list:
		quote_list.remove("")
	if not scan:
		quote=quote_list[0]
	else:
		keyword_quotes=[i for i in quote_list if scan in i]
		em=discord.Embed(title="Matching quotes")
		em.add_field(name="Number of Quotes",value=len(quote_list))
		em.add_field(name="Number of Matching Quotes",value=len(keyword_quotes))
		if len(keyword_quotes)==0:
			return "No matching quotes"
		random.shuffle(keyword_quotes)
		while keyword_quotes[0] in used_quotes:
			keyword_quotes.remove(keyword_quotes[0])
		quote=keyword_quotes[0]
		em.add_field(name="One of the Matching Quotes",value=quote)
	for i in used_quotes:
		if i in quote_list:
			quote_list.remove(i)
	random.shuffle(quote_list)
	with open("text_files/quotes","w") as quotes_file:
		quotes_file.writelines(quote_list)
	with open("text_files/used_quotes","a") as used_quotes_file:
		used_quotes_file.write(quote)
	if scan:
		return em
	return quote

def set_day_type():
	if rn("%a")in "SatSun":
		with open("text_files/day_type","w") as day_type_file:
			day_type_file.write("off")
	with open("text_files/special_days") as special_day_file:
		special_days=special_day_file.readlines()
	for i in special_days:
		if rn("%m/%d")==i.split(":")[0]:
			with open("text_files/day_type","w") as day_type:
				day_type.write(i.split(":")[1])
			return
	with open("text_files/day_type","w") as day_type:
		day_type.write("norm")

def get_day_type():
	with open("text_files/day_type") as day_type_file:
		day_type=day_type_file.readline()
	if day_type!="":
		day_type=day_type.split("\n")[0]
	else:
		set_day_type()
		with open("text_files/day_type") as day_type_file:
			day_type=day_type_file.readline()
	return day_type

def daily_funcs():
	os.remove("text_files/cancel")
	open("text_files/cancel","x")
	set_day_type()
	setup_lunches()

def num_suffix(num):
	num=str(int(num))
	if len(num)>2:
		num=num[len(num)-2:]
	if num in ["1","21","31"]: return "st"
	if num in ["2","22","32"]: return "nd"
	if num in ["3","23","33"]: return "rd"
	return "th"

def type_checker(var,assumed_type=None):
	if assumed_type==None:
		return(str(type(var))[8:-2])
	return assumed_type in str(type(var))


def setup_lunches():
	with open("text_files/raw_lunches") as lunch_file:
		raw_lunches=lunch_file.readlines()
	days=[]
	day_num=-1
	food=False
	for item in raw_lunches: #splits by days
		item=item.replace("\n","").lower()
		if item.split(" ")[0] in months:
			item=item.split(" ")
			days.append(f"{item[0]}/{item[1]}:")
			food=True
			day_num+=1
		elif food:
			days[day_num]+=item
			food=False
	days=list(set(days))
	for i,school_day in enumerate(days): # filters food items
		day=school_day.split(":")[0]+":"
		food=school_day.split(":")[1]
		good=True
		for bad in no_eat:
			if bad in food:
				good=False
		if good:
			day+=food
		days[i]=day
	for i,menu_item in enumerate(days):# final formatting and organizing with days
		day=menu_item.split(":")[0]
		food=menu_item.split(":")[1]
		if " with" in food:
			food=food.split(" with")[0]
		if " on" in food:
			food=food.split(" on")[0]
		if " and" in food:
			food=food.split(" and")[0]
		if int(day.split("/")[1])<10:
			day=day.replace("/","/0")
		days[i]=f"{day}:{food}".replace(":,",":").replace("  "," ")
		if food=="":
			days[i]+="Chicken Patty"
		days[i]+="\n"
	month=rn("%B").lower()
	menu=[]
	for i,day in enumerate(days):
		good=True
		for x in ["dismissal","school","2021","2022"]:
			if x in day:
				good=False
		day=day.split(":")[0]
		if months.index(day.split("/")[0])<months.index(month):
			continue
		elif int(day.split("/")[1])<int(rn("%d")) and day.split("/")[0]==month:
			continue
		elif good:
			final=days[i].split(":")
			final[1]=final[1].title().replace("Bbq","BBQ").replace("Np","NP")
			menu.append(":".join(final))
	menu.sort()
	with open("text_files/lunches","w") as lunch_file:
		lunch_file.writelines(menu)

async def event_loop():
	await client.wait_until_ready()
	while not client.is_closed():
		if client.is_ws_ratelimited():
			await client.close()
		channel=client.get_channel(801836482960556133)
		day_type=get_day_type()
		letr_day=letter_day()
		if during_school("day") and letr_day!="error":
			response=schedule(day_type,letr_day)
			if type_checker(response,"list"):
				for i in response:
					await channel.send(i)
				await asyncio.sleep(50)
			elif type_checker(response,"str") and response!="error":
				await channel.send(response)
				await asyncio.sleep(50)
		if(rn()=="06:18" and during_school("day"))or(rn()=="10:30"and not during_school("day")):
			if log_command("morning"):
				await asyncio.sleep(60)
			else:
				try:
					em=formatted_weather("Good Morning",discord.Color.orange(),"Download Morning Wire!")
				except:
					em=discord.Embed(title="Good Morning",color=discord.Color.orange())
				day_num=int(rn("%d"))
				suffix=num_suffix(int(rn("%d")[1]))
				em.insert_field_at(0,name="Today is",value=rn(f"%A, %B {day_num}{suffix}"))
				if during_school("day") and letr_day!="error":
					em.insert_field_at(1,name="Letter Day",value=letr_day)
				await channel.send(content=weather_emoji(),embed=em)
				with open("text_files/errors") as errors:
					error_list=list(errors.readlines())
					if len(error_list)>100000:
						await channel.send("OVER 100,000 ERRORS, FIX IMMEDIATELY!")
					elif len(error_list)>1000:
						await channel.send("Over 10,000 errors, fix it soon.")
					elif len(error_list)>1000:
						await channel.send("Over 1,000 erros, check it out sometime soon.")
				await asyncio.sleep(50)
		if (rn()=="06:40" and during_school("day")) or (rn()=="11:00" and not during_school("day")):
			if log_command("morning quote"):
				await asyncio.sleep(1)
			else:
				await channel.send(get_quote())
				await asyncio.sleep(50)
		elif rn("%H") in "0103": # daily operations
			daily_funcs()
		await asyncio.sleep(5)
client.loop.create_task(event_loop())
client.run(os.getenv("TOKEN"))


'''
	to maybe add later for economy bot

multiple banks
bank fees
loans
higher/lower
bank heists
blackjack
credit scores

'''
