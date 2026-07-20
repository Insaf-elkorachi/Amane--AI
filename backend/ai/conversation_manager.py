class ConversationManager:

    def process(self, conversation_id, message):

        message = message.lower()

        # Première version très simple

        if "trou" in message:

            return {
                "conversation_id": 1,
                "reply": "Pouvez-vous préciser l'emplacement exact du trou ?",
                "finished": False
            }

        if "fuite" in message:

            return {
                "conversation_id": 1,
                "reply": "La fuite concerne quel équipement ?",
                "finished": False
            }

        if "électricité" in message or "electrique" in message:

            return {
                "conversation_id": 1,
                "reply": "Le danger est-il toujours présent ?",
                "finished": False
            }

        return {
            "conversation_id": 1,
            "reply": "Pouvez-vous décrire davantage le problème observé ?",
            "finished": False
        }