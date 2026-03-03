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
        """
        token: Token de Telegram.
        controlador: Tu controlador principal RAG.
        lista_bots: Lista de strings ['Bot1', 'Bot2', ...] para el menú.
        """
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
        """Maneja el clic en el botón (CallbackQuery)."""
        query = update.callback_query
        await query.answer()

        nombre_bot = query.data.replace("select_", "")
        context.user_data['bot_actual'] = nombre_bot

        try:
            await query.edit_message_text(
                text=f"✅ Has seleccionado a: *{nombre_bot}*\n\nYa puedes hacerme preguntas.",
                parse_mode='Markdown'
            )
        except Exception:
            # Si el mensaje ya dice lo mismo, Telegram da error al editar, así lo ignoramos
            pass

    async def responder_a_pregunta(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Responde usando la lógica de procesar_consulta_bot."""
        # 1. Recuperamos el nombre del bot que el usuario eligió previamente
        bot_seleccionado = context.user_data.get('bot_actual')

        if not bot_seleccionado:
            await update.message.reply_text("⚠️ Por favor, selecciona un asistente primero con /start")
            return

        user_text = update.message.text

        # 2. Mensaje visual de "escribiendo..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        mensaje_espera = await update.message.reply_text(f"🔎 {bot_seleccionado} está consultando los documentos...")

        try:
            # 3. LLAMADA A LA NUEVA FUNCIÓN
            # Usamos la función que acabamos de crear: procesar_consulta_bot
            # Solo le pasamos: nombre_bot y pregunta
            respuesta_gemini = await asyncio.to_thread(
                self.controlador.procesar_consulta_bot, 
                bot_seleccionado, # nombre_bot
                user_text         # pregunta
            )

            # 4. Enviamos la respuesta final
            if respuesta_gemini:
                await update.message.reply_text(respuesta_gemini)
            else:
                await update.message.reply_text("No he podido obtener una respuesta válida.")

        except Exception as e:
            print(f"❌ Error en Telegram: {e}")
            await update.message.reply_text(f"Lo siento, ocurrió un error técnico: {e}")
        
        finally:
            # Opcional: Borrar el mensaje de "pensando..." para no ensuciar el chat
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
        