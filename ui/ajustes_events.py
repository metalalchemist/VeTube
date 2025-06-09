# -*- coding: UTF-8 -*-

import wx # For event type hints if used, and wx constants
from utils import languageHandler, fajustes, app_utilitys
from TTS.list_voices import piper_list_voices, install_piper_voice
# from helpers.sound_helper import playsound # playsound instance will be passed
# from helpers.reader_handler import ReaderHandler # ReaderHandler instance will be passed

_ = languageHandler.language.gettext

class ConfiguracionDialogEvents:
	def alternar_dispositivo(self, event, ui_elements, config, player, reader_handler, global_refs):
		# ui_elements should have: lista_dispositivos
		# global_refs should have: dispositivos_piper
		valor = (ui_elements.lista_dispositivos.GetSelection() +1)
		valor_str = ui_elements.lista_dispositivos.GetStringSelection()
		config['dispositivo']=valor
		player.setdevice(config["dispositivo"])
		player.playsound("sounds/cambiardispositivo.wav")
		if config['sistemaTTS'] == "piper" and global_refs.get('dispositivos_piper') is not None:
			salida_piper = reader_handler._lector.find_device_id(valor_str)
			reader_handler._lector.set_device(salida_piper)
			reader_handler.leer_auto(_("Hablaré a través de este dispositivo."))
		return config # Return modified config

	def cambiar_sintetizador(self, event, ui_elements, config, reader_handler, global_refs):
		# ui_elements should have: seleccionar_TTS, instala_voces, choice_2
		# global_refs should have: lista_voces, lista_voces_piper
		config['sistemaTTS']=ui_elements.seleccionar_TTS.GetStringSelection()
		current_lista_voces = global_refs.get('lista_voces', [])
		if config['sistemaTTS'] == "piper":
			lista_voces_piper_val = global_refs.get('lista_voces_piper')
			if not lista_voces_piper_val is None:
				current_lista_voces = lista_voces_piper_val
			else:
				current_lista_voces = [_("No hay voces instaladas")]
			ui_elements.instala_voces.Enable()
			ui_elements.slider_1.Disable() # Pitch
			ui_elements.label_8.Disable()
			ui_elements.slider_2.Disable() # Volume
			ui_elements.label_9.Disable()
		else:
			current_lista_voces = reader_handler._leer.list_voices() # Accessing original SAPI/Screenreader voices
			ui_elements.instala_voces.Disable()
			ui_elements.slider_1.Enable()  # Pitch
			ui_elements.label_8.Enable()
			ui_elements.slider_2.Enable()  # Volume
			ui_elements.label_9.Enable()

		ui_elements.choice_2.Clear()
		ui_elements.choice_2.AppendItems(current_lista_voces)
		if current_lista_voces: # Ensure there's something to select
			ui_elements.choice_2.SetSelection(0) # Default to first voice
			config['voz'] = 0 # Update config

		global_refs['lista_voces'] = current_lista_voces # Update the shared reference if necessary
		return config, global_refs # Return modified config and global_refs

	def instalar_voz_piper(self, event, ui_elements, config, reader_handler, global_refs):
		# ui_elements should have: choice_2
		# global_refs should have: lista_voces, lista_voces_piper
		# install_piper_voice might need to return the updated reader_handler._lector if it changes it internally.
		# For now, assuming it modifies reader_handler._lector directly or config holds all state.
		config, reader_handler._lector = install_piper_voice(config, reader_handler._lector)
		global_refs['lista_voces_piper'] = piper_list_voices() # Refresh the list of piper voices
		current_lista_voces = global_refs.get('lista_voces_piper', [])

		if current_lista_voces:
			ui_elements.choice_2.Clear()
			ui_elements.choice_2.AppendItems(current_lista_voces)
			ui_elements.choice_2.SetSelection(0) # Default to first voice
			config['voz'] = 0 # Update config
		else: # No voices after install? Clear and show message.
			ui_elements.choice_2.Clear()
			ui_elements.choice_2.Append(_("No hay voces instaladas"))
			ui_elements.choice_2.SetSelection(0)


		global_refs['lista_voces'] = current_lista_voces # Update the main voice list for the UI
		return config, reader_handler, global_refs

	def reproducirPrueva(self, event, ui_elements, config, reader_handler, global_refs):
		# ui_elements should have: choice_2
		# global_refs should have: lista_voces
		selected_voice_name = ""
		if global_refs.get('lista_voces') and len(global_refs.get('lista_voces')) > ui_elements.choice_2.GetSelection():
			selected_voice_name = global_refs.get('lista_voces')[ui_elements.choice_2.GetSelection()]

		text_to_speak = _("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos.")
		if config['sistemaTTS'] == "piper": # or ".onnx" in selected_voice_name if that's more reliable
			reader_handler.leer_auto(text_to_speak)
		else: # SAPI or other non-Piper screen reader
			reader_handler._leer.silence() # Stop previous speech if any
			reader_handler.leer_sapi(text_to_speak)


	def cambiarVelocidad(self, event, ui_elements, config, reader_handler, global_refs):
		# ui_elements should have: slider_3, choice_2
		# global_refs should have: lista_voces
		value=ui_elements.slider_3.GetValue()-10
		selected_voice_name = ""
		if global_refs.get('lista_voces') and len(global_refs.get('lista_voces')) > ui_elements.choice_2.GetSelection():
			selected_voice_name = global_refs.get('lista_voces')[ui_elements.choice_2.GetSelection()]

		if config['sistemaTTS'] == "piper": # or ".onnx" in selected_voice_name:
			# Ensure app_utilitys.porcentaje_a_escala is appropriate for Piper's rate.
			# Piper rate is a float multiplier (e.g., 1.0 is normal, 0.5 is half speed).
			# Slider is 0-20, so value is -10 to 10.
			# This needs careful mapping. Assuming 0 is normal (1.0x), +10 is fastest, -10 is slowest.
			# Example mapping: if value 0 -> 1.0x, value 10 -> 2.0x, value -10 -> 0.5x
			# This is an assumption, the actual piper set_rate might expect different values.
			scaled_value = 1.0 + (value / 10.0) * 0.5 # e.g. value 10 -> 1.5x, value -10 -> 0.5x. Adjust as needed.
			reader_handler._lector.set_rate(scaled_value)
		else:
			reader_handler._leer.set_rate(value)
		config['speed']=value
		return config

	def cambiarTono(self, event, ui_elements, config, reader_handler):
		# ui_elements should have: slider_1
		# This likely only applies to SAPI voices, Piper might not support pitch.
		value=ui_elements.slider_1.GetValue()-10
		if config['sistemaTTS'] != "piper": # Guard against applying to Piper if not supported
			reader_handler._leer.set_pitch(value)
		config['tono']=value
		return config

	def cambiarVolumen(self, event, ui_elements, config, reader_handler):
		# ui_elements should have: slider_2
		# This likely only applies to SAPI voices, Piper might not support volume this way.
		value = ui_elements.slider_2.GetValue()
		if config['sistemaTTS'] != "piper": # Guard against applying to Piper if not supported
			reader_handler._leer.set_volume(value)
		config['volume']=value
		return config

	def mostrarSonidos(self,event, ui_elements, config):
		# ui_elements should have: soniditos, reproducir
		is_checked = event.IsChecked()
		config['sonidos']=is_checked
		ui_elements.soniditos.Enable(is_checked)
		ui_elements.reproducir.Enable(is_checked)
		return config

	def checar(self, event, key_to_check, config):
		config[key_to_check]=True if event.IsChecked() else False
		return config

	def checar_sapi(self, event, ui_elements, config):
		# ui_elements should have: seleccionar_TTS, check_1 (the sapi checkbox itself)
		is_checked = event.IsChecked() # or ui_elements.check_1.IsChecked()
		config['sapi']=is_checked
		ui_elements.seleccionar_TTS.Enable(not is_checked)
		# If SAPI is checked, perhaps force TTS system to sapi5 and update voice list?
		if is_checked:
			config['sistemaTTS'] = "sapi5" # Or whatever the SAPI identifier is
			# This implies a call similar to cambiar_sintetizador logic to update voices
			# For simplicity, this side effect is noted but not fully implemented here to avoid circular calls
			# or making this method too complex. The main class would coordinate this.
			ui_elements.seleccionar_TTS.SetStringSelection(config['sistemaTTS'])
		return config


	def cambiarVoz(self, event, ui_elements, config, reader_handler, global_refs):
		# ui_elements should have: choice_2, lista_dispositivos
		# global_refs should have: lista_voces, dispositivos_piper
		# reader_handler is 'prueba' from the original code

		config['voz']=ui_elements.choice_2.GetSelection()
		current_lista_voces = global_refs.get('lista_voces', [])

		if not current_lista_voces or config['voz'] >= len(current_lista_voces):
			# Voice selection is out of bounds, possibly due to list update.
			# Handle gracefully, maybe select first voice or do nothing.
			return config, reader_handler, global_refs


		selected_voice_identifier = current_lista_voces[config['voz']]

		if config['sistemaTTS'] == "piper":
			# Assuming selected_voice_identifier is the ONNX file name like "model.onnx"
			# and the path structure is known e.g. f"piper/voices/voice-{selected_voice_identifier[:-5]}/{selected_voice_identifier}"
			# The original code was: f"piper/voices/voice-{lista_voces[config['voz']][:-5]}/{lista_voces[config['voz']]}"
			# This needs the base name of the voice model.
			if ".onnx" in selected_voice_identifier:
				voice_model_path = f"piper/voices/voice-{selected_voice_identifier.replace('.onnx','')}/{selected_voice_identifier}"
				reader_handler._lector = reader_handler._lector.piperSpeak(voice_model_path) # This might re-initialize the lector
				global_refs['dispositivos_piper'] = reader_handler._lector.get_devices() # Update piper devices

				# Set device based on current selection in UI for audio output
				# ui_elements.dispositivos is the choices for wx.Choice, not the control itself
				# Assuming ui_elements.lista_dispositivos.GetStringSelection() gives the device name string
				if hasattr(ui_elements, 'dispositivos') and config["dispositivo"]-1 < len(ui_elements.dispositivos):
					selected_device_name = ui_elements.dispositivos[config["dispositivo"]-1]
					salida_piper = reader_handler._lector.find_device_id(selected_device_name)
					reader_handler._lector.set_device(salida_piper)
		else:
			# For SAPI or other screen readers
			reader_handler._leer.set_voice(selected_voice_identifier)

		return config, reader_handler, global_refs

	def on_list_item_checked(self, event, list_ctrl_name, config_key, config):
		# Generic handler for ListCtrl item checks (e.g., self.categoriza, self.soniditos, self.eventos, self.unread)
		# list_ctrl_name is the name of the list_ctrl in ui_elements
		# config_key is the key in config dictionary (e.g., 'categorias', 'listasonidos')
		# This method was not in the original list but is implied by ListCtrl with checkboxes
		item_index = event.GetIndex()
		is_checked = event.GetEventObject().IsItemChecked(item_index)

		if config_key in config and isinstance(config[config_key], list) and 0 <= item_index < len(config[config_key]):
			config[config_key][item_index] = is_checked
		return config

	def on_tree_page_changing(self, event, ui_elements):
		# Example: if there's logic needed when a treebook page changes
		# old_selection = event.GetOldSelection()
		# new_selection = event.GetSelection()
		# page = ui_elements.tree_1.GetPage(new_selection)
		# page_title = ui_elements.tree_1.GetPageText(new_selection)
		# print(f"Changing to page: {page_title}")
		event.Skip() # Allow page change

	# Method for handling OK button (applying changes)
	def on_ok(self, event, config_to_save):
		fajustes.escribirConfiguracion(config_to_save)
		if hasattr(event, 'GetEventObject') and isinstance(event.GetEventObject(), wx.Dialog):
			dialog = event.GetEventObject()
			dialog.EndModal(wx.ID_OK)
		elif isinstance(event, wx.Dialog): # If dialog itself is passed
			event.EndModal(wx.ID_OK)


	# Method for handling Cancel button
	def on_cancel(self, event):
		if hasattr(event, 'GetEventObject') and isinstance(event.GetEventObject(), wx.Dialog):
			dialog = event.GetEventObject()
			dialog.EndModal(wx.ID_CANCEL)
		elif isinstance(event, wx.Dialog): # If dialog itself is passed
			event.EndModal(wx.ID_CANCEL)

	def on_choice_language(self, event, ui_elements, config):
		# ui_elements.choice_language, ui_elements.codes, ui_elements.langs
		selected_lang_name = ui_elements.choice_language.GetStringSelection()
		# Assuming ui_elements.codes and ui_elements.langs are available, containing language codes and names
		# These would need to be populated and passed within ui_elements if not globally available.
		# For this example, let's assume they are on ui_elements.
		if hasattr(ui_elements, 'langs') and hasattr(ui_elements, 'codes'):
			try:
				lang_index = ui_elements.langs.index(selected_lang_name)
				config['idioma'] = ui_elements.codes[lang_index] # codes were reversed in original
			except ValueError:
				pass # Language name not found
		return config

	def on_choice_translate_to(self, event, ui_elements, config):
		# ui_elements.choice_traducir
		# This choice was populated with translator.LANGUAGES keys
		# The config implications need to be defined (e.g., config['translate_to_lang'])
		selected_translation_lang = ui_elements.choice_traducir.GetStringSelection()
		# Example: config['translate_to_lang_name'] = selected_translation_lang
		# Find code if needed:
		# for code, name in translator.LANGUAGES.items(): # translator instance needed
		# if name == selected_translation_lang:
		# config['translate_to_lang_code'] = code
		# break
		# For now, just storing the name. A translator instance would be needed for code lookup.
		config['translate_to_language_name'] = selected_translation_lang
		return config

	def on_choice_currency(self, event, ui_elements, config):
		# ui_elements.choice_moneditas
		# This was populated with CODES. CODES[k], ({k})
		selection = ui_elements.choice_moneditas.GetStringSelection()
		if selection == _('Por defecto'):
			config['target_currency'] = None
		else:
			# Extract currency code like "USD" from "US Dollar, (USD)"
			import re
			match = re.search(r'\((\w+)\)', selection)
			if match:
				config['target_currency'] = match.group(1)
		return config

	def on_play_sound_button(self, event, ui_elements, player, global_refs):
		# ui_elements.soniditos
		# global_refs.rutasonidos
		focused_item_index = ui_elements.soniditos.GetFocusedItem()
		if focused_item_index != -1 and global_refs.get('rutasonidos') and focused_item_index < len(global_refs.get('rutasonidos')):
			sound_path = global_refs.get('rutasonidos')[focused_item_index]
			player.playsound(sound_path, False)

```
