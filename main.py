from core import handle_command

if __name__ == "__main__":
    # Startup message
    handle_command("startup", chat_id="laptop")

    while True:
        user_input = input("YOU (Laptop): ")
        if user_input.strip():
            handle_command(user_input, chat_id="laptop")
