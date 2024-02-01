import os
import telebot
import requests
import aiohttp
import asyncio

# The API Key we received for our bot
# Define your bot token here
BOT_TOKEN = '6699324943:AAFUMvb9HT_VGato2AowbBdQ9TzrpUhleYg'

ADMIN_CHAT_ID = 5648376510  # Replace with your admin chat ID
IMAGE_LIMIT = 20

bot = telebot.TeleBot(BOT_TOKEN)

# The URL and headers for the Prodia API
PRODIA_URL = "https://api.prodia.com/v1/sd/generate"
PRODIA_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-Prodia-Key": "0a145a11-ce7e-4c60-a61e-ceea85584913"
}

# Dictionary to store the number of image generations for each user
user_image_count = {}

# A function to make a POST request to the Prodia API
async def post_request(url, payload, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()

# A function to get the status of a job from the Prodia API
async def get_status(url, headers, job_id):
    status_url = f"https://api.prodia.com/job/{job_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(status_url, headers=headers) as response:
            return await response.json()

# A function to run the main logic of the bot
async def main(message, user_input):
    # Check if the user has exceeded the image generation limit
    user_id = message.from_user.id
    if user_id not in user_image_count:
        user_image_count[user_id] = 0

    if user_id != ADMIN_CHAT_ID and user_image_count[user_id] >= IMAGE_LIMIT:
        bot.send_message(message.chat.id, f"Sorry, you have reached the maximum limit of {IMAGE_LIMIT} image generations.")
        return

    # Increment the image count for the user
    user_image_count[user_id] += 1

    # Predefined syntax to prepend before user input
    predefined_syntax = "Nude, Undress"

    # Combine the predefined syntax and user input for the prompt
    prompt = f"{predefined_syntax} {user_input}"

    # Create the payload for the Prodia API
    payload = {
        "model": "epicrealism_naturalSinRC1VAE.safetensors [90a4c676]",
        "prompt": prompt,
        "negative_prompt": "badly drawn, (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation",
        "steps": 26,
        "cfg_scale": 5,
        "sampler": "DPM++ 2M Karras",
        "aspect_ratio": "portrait"
    }

    # Make the initial POST request
    data = await post_request(PRODIA_URL, payload, PRODIA_HEADERS)
    job_id = data.get("job")  # Get the job ID from the response

    # Show a loader on the user's chat
    loader_message = bot.reply_to(message, text="Generating image...")

    try:
        # Check the status in a loop until it's no longer 'generating'
        while True:
            status_data = await get_status(PRODIA_URL, PRODIA_HEADERS, job_id)
            status = status_data.get("status")

            if status == "succeeded":
                image_url = f"https://images.prodia.xyz/{job_id}.png"
                # Send the image to the user
                bot.send_photo(message.chat.id, image_url)
                # Hide the loader on the user's chat
                bot.delete_message(message.chat.id, loader_message.message_id)
                # Send a message indicating the image is generated
                bot.send_message(message.chat.id, "Image generated, Motherfucker!")
                break  # Exit the loop if the status is 'succeeded'
            elif status != "generating":
                # Send an error message to the user
                bot.send_message(message.chat.id, "Job failed or completed with an error.")
                # Hide the loader on the user's chat
                bot.delete_message(message.chat.id, loader_message.message_id)
                break  # Exit the loop if the status is not 'generating'

            await asyncio.sleep(2)  # Sleep for a short duration before checking again

    except telebot.apihelper.ApiTelegramException as e:
        print(f"Telegram API Exception: {e}")
        bot.send_message(message.chat.id, "An unexpected error during image generation.")
        # Handle the exception as needed, for example, logging or notifying the user
        
# A handler for the /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "😒 Welcome Fuckkers Remove Clothes of Anyone. Also I can generate realistic images based on your text input. To use me, just type /gen followed by your prompt. For example: /gen A hairy girl")

# A handler for the /mot command
@bot.message_handler(commands=['gen'])
def send_mot(message):
    # Get the prompt from the message
    try:
        prompt = message.text.split("/gen ", 1)[1]
        # Run the main function with the message and the prompt
        asyncio.run(main(message, prompt))
    except IndexError:
        # Send a message to the user if no prompt is given
        bot.send_message(message.chat.id, "Please provide a prompt after the /gen command.")

# A handler for the /status command
@bot.message_handler(commands=['status'])
def send_status(message):
    user_id = message.from_user.id
    if user_id == ADMIN_CHAT_ID:
        status_message = (
            "Image generation status:\n"
            f"Image Limit: Infinite\n"
            f"Bot Status: \U0001F44D (thumbs up)"
        )
    else:
        status_message = (
            "Image generation status:\n"
            f"Image Limit: {IMAGE_LIMIT}\n"
            f"Your Image Count: {user_image_count.get(user_id, 0)}\n"
            f"Bot Status: \U0001F44D Fucking Good"
        )

    bot.send_message(message.chat.id, status_message)

# A handler for the /undress command
@bot.message_handler(commands=['undress'])
def send_undress(message):
    user_id = message.from_user.id
    if user_id == ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "Next week setting in GPU.")
    else:
        bot.send_message(message.chat.id, "Next week setting in GPU.")

# Start polling for updates
bot.polling()
