# Spotify Stalker
Discord Selfbot to evaluate what your friends are listening to.

⚠️ This is a so called 'SelfBot' and agains the TOS of `Discord Inc.`  
➡️ See [Discord Terms](https://discord.com/terms) (https://discord.com/terms)  
**Use on own Risk!**

## Requirements
- Have a MongoDB
- The target user's need to be added as your friends
    - This Bot checks the Presence of the target. Make sure you can see it
- Discord Token Authorization key

## Environment
#### Token
**Key:** `TOKEN`  
This is required for the Authentication with Discord
#### Mongo URI
**Key:** `MONGO_URI`  
This is required for the Database authentication and storing the obtained data
#### Targets
**Key:** `TARGET_USERS`  
This is required for filtering the Users. If empty, the will be no filter.
If you want to pass multiple ID's, add a trailing `,`  
⚠️ **NO SPACES!**
#### Mongo Database
**Key:** `MONGO_DATABASE`   
**Default:** `spotify_checker`  
In which database the data should be written into

## Data
The data obtained will be stored inside a Database
