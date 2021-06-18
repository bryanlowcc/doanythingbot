from datetime import datetime
import getpass
       
time = int(datetime.now().strftime("%H"))
user = getpass.getuser()

if time >= 5 and time < 12:
    print(f"Good Morning {user}! How may I assist you today?")

elif time >= 12 and time < 17:
    print(f"Good Afternoon {user}! How may I assist you today?")

else:
    print(f"Good Evening {user}! How may I assist you today?")

# import getpass

# user = getpass.getuser()

# print(user)