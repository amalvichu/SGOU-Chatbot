from django.core.management.base import BaseCommand
from Chatbot.knowledge_base.fetch_and_embed import fetch_data, generate_embeddings

class Command(BaseCommand):
    help = 'Updates the vector DB for SGOU programs'

    def handle(self, *args, **kwargs):
        fetch_data()
        generate_embeddings()
        self.stdout.write(self.style.SUCCESS('✅ Program vector DB updated.'))
