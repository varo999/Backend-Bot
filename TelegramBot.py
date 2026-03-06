import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    PicklePersistence
)
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler


class TelegramBot:
    def __init__(self, token: str, controlador, lista_bots: list):
        persistence = PicklePersistence(filepath="user_data.pkl")
        
        self.app = (
            ApplicationBuilder()
            .token(token)
            .persistence(persistence)
            .build()
        )
        
        self.controlador = controlador
        self.lista_bots = lista_bots  
        self._add_handlers()

    def _add_handlers(self):
        """Método privado para agregar todos los handlers."""
        self.app.add_handler(CommandHandler("start", self.start))
        
        # --- ESTA ES LA LÍNEA QUE FALTA ---
        # Registra el manejador para los clics en los botones Inline
        self.app.add_handler(CallbackQueryHandler(self.seleccionar_asistente))
        # ----------------------------------
        
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.responder_a_pregunta)
        )
        
        self.app.add_error_handler(self.error_handler)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Muestra el menú de selección de asistentes."""
            if not self.lista_bots:
                await update.message.reply_text("❌ No hay asistentes configurados.")
                return

            # Creamos los botones dinámicamente
            keyboard = [
                [InlineKeyboardButton(nombre, callback_data=f"select_{nombre}")]
                for nombre in self.lista_bots
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            saludo = f'¡Hola, {update.effective_user.first_name}! 👋\nSelecciona el asistente:'
            await update.message.reply_text(saludo, reply_markup=reply_markup)

    async def seleccionar_asistente(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja el clic en el botón y crea la conversación en la BD."""
        query = update.callback_query
        await query.answer()

        nombre_bot = query.data.replace("select_", "")
        
        # 1. Creamos la conversación en la BD para este usuario de Telegram
        id_telegram = str(update.effective_user.id)
        id_nueva_conv = self.controlador.guardar_conversacion(nombre_bot, id_usuario=id_telegram)

        if id_nueva_conv:
            # 2. Guardamos AMBOS en la sesión de Telegram del usuario
            context.user_data['bot_actual'] = nombre_bot
            context.user_data['id_conv_actual'] = id_nueva_conv

            await query.edit_message_text(
                text=f"✅ Has seleccionado a: *{nombre_bot}*\n\nSe ha iniciado una nueva sesión (ID: {id_nueva_conv}). Ya puedes preguntar.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(text="❌ Error al iniciar conversación con el bot.")

    async def responder_a_pregunta(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Responde usando el ID de conversación guardado en user_data."""
        bot_seleccionado = context.user_data.get('bot_actual')
        id_conv = context.user_data.get('id_conv_actual') # <--- Recuperamos el ID de la BD

        if not bot_seleccionado or not id_conv:
            await update.message.reply_text("⚠️ Por favor, selecciona un asistente primero con /start")
            return

        user_text = update.message.text
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        mensaje_espera = await update.message.reply_text(f"🔎 {bot_seleccionado} está consultando...")

        try:
            # Llamamos al controlador pasando el ID de la conversación
            respuesta_gemini = await asyncio.to_thread(
                self.controlador.procesar_consulta_bot, 
                bot_seleccionado, 
                user_text,
                id_conv  # <--- Pasamos el ID para que guarde y lea el historial
            )

            if respuesta_gemini:
                await update.message.reply_text(respuesta_gemini)
            else:
                await update.message.reply_text("No he podido obtener una respuesta.")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
        finally:
            await mensaje_espera.delete()
   
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler que registra los errores causados por los Updates."""
        print(f"Update '{update}' causó error: {context.error}", file=sys.stderr)

    def actualizar_lista_desde_controlador(self):
        """
        Sincroniza la lista interna de bots con los que están 
        actualmente cargados en el controlador de memoria.
        """
        # Extraemos las llaves (nombres) del diccionario del controlador de bots
        nuevos_nombres = list(self.controlador.controlador_bots.diccionario_bots.keys())
        
        # Actualizamos la variable que usa el menú de botones
        self.lista_bots = nuevos_nombres
        
        print(f"🔄 [TELEGRAM] Lista sincronizada. Bots disponibles: {len(self.lista_bots)}")
        return self.lista_bots
    
    def run(self):
        """Método para iniciar el bot correctamente en un hilo."""
        print("Bot iniciado (clase TelegramBot), esperando mensajes...")
        
        # Creamos un nuevo bucle de eventos para este hilo específico
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ejecutamos el polling dentro de ese bucle
        self.app.run_polling(close_loop=False)
        