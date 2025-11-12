from instagrapi import Client


cl = Client()
login = input("Login: ")
password = input("Password: ")
cl.login(login, password)
cl.dump_settings('authorize.json')