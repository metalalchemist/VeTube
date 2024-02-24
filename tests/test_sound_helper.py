from helpers.sound_helper import playsound

ps = playsound()

device_names = ps.devicenames
print(device_names)
#print("Dispositivos disponibles:")
for i, name in enumerate(device_names):
	ps.setdevice(i+1)
	print(f"Dispositivo establecido: {device_names[i-1]}")
	file_to_play = "sounds/abrirchat.wav"
	ps.playsound(file_to_play, True)
	#print(f"reproducido el sonido en el dispositivo {device_names[i-1]}.")