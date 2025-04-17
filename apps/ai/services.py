import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from apps.destinations.models import Destinations
from apps.fauna.models import Fauna
from apps.flora.models import Flora
from apps.health.models import Health
from apps.kuliner.models import Kuliner
import random
import re

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.API_GEMINI_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.history_length = 5
        
        # Template untuk respons yang lebih ramah
        self.friendly_responses = {
            'not_found': [
                "Wah, untuk {} belum ada di database nih. Tapi aku bisa kasih tau tentang {} yang menarik di Bogor! 😊",
                "Hmm, untuk {} sepertinya belum tersedia. Tapi yuk, aku ceritakan tentang {} seru di Bogor! 😉",
                "Untuk {} belum ada di sistem nih. Tapi tenang, aku punya rekomendasi {} keren di Bogor! 🌟"
            ],
            'greeting': [
                "Hai! Saya Celya, asisten virtual yang siap membantu Anda menjelajahi keindahan alam dan budaya Bogor. ",
                "Hai! Saya Celya, senang bisa membantu Anda menemukan pengalaman wisata yang menakjubkan di Bogor. ",
                "Hai! Saya Celya, siap menemani petualangan Anda dalam menjelajahi destinasi-destinasi menarik di Bogor. "
            ],
            'follow_up': [
                "Ada yang ingin Anda ketahui lebih detail?",
                "Mau tahu lebih banyak tentang hal lainnya?",
                "Ada yang masih ingin Anda tanyakan?"
            ]
        }

    def _get_conversation_history(self, session_id):
        """Get conversation history from cache"""
        return cache.get(f'chat_history_{session_id}', [])
    
    def _update_conversation_history(self, session_id, user_input, response):
        """Update conversation history in cache"""
        history = self._get_conversation_history(session_id)
        history.append({
            'user': user_input,
            'assistant': response['text'],
            'intent': response['intent'],
            'references': response['content_references']
        })
        
        # Keep only last N conversations
        if len(history) > self.history_length:
            history = history[-self.history_length:]
            
        # Set cache with 30 minutes expiry
        cache.set(f'chat_history_{session_id}', history, 1800)
        
    def _format_conversation_history(self, history):
        """Format conversation history for context"""
        formatted = []
        for conv in history:
            formatted.append(f"User: {conv['user']}")
            formatted.append(f"Assistant: {conv['assistant']}")
            # Tambahkan informasi referensi jika ada
            if conv.get('references'):
                refs = [ref['name'] for ref in conv['references']]
                formatted.append(f"Referenced Items: {', '.join(refs)}")
        return "\n".join(formatted)

    def _get_model_data(self, model, type_name):
        items = []
        for item in model.objects.all():
            data = {
                'type': type_name,
                'id': item.id,
                'title': item.title,
                'description': item.description
            }
            
            # Pengaturan konten berdasarkan tipe data
            if type_name == 'destination':
                if hasattr(item, 'location'):
                    data['location'] = item.location
                    data['content'] = (
                        f"Destinasi: {item.title}\n"
                        f"Lokasi: {item.location}\n"
                        f"Deskripsi: {item.description}\n"
                    )
            elif type_name == 'culinary':
                # Khusus untuk kuliner, tambahkan informasi spesifik
                data['content'] = (
                    f"Kuliner: {item.title}\n"
                    f"Deskripsi: {item.description}\n"
                    f"Lokasi: {item.location if hasattr(item, 'location') else 'Bogor'}\n"
                    f"Karakteristik: Makanan khas Bogor\n"
                )
            elif type_name == 'health':
                # Khusus untuk informasi kesehatan
                data['content'] = (
                    f"Informasi Kesehatan: {item.title}\n"
                    f"Detail: {item.description}\n"
                    f"Lokasi Fasilitas: {item.location if hasattr(item, 'location') else 'Bogor'}\n"
                    f"Kategori: Layanan Kesehatan Bogor\n"
                )
            elif type_name == 'flora':
                # Khusus untuk flora
                data['content'] = (
                    f"Flora: {item.title}\n"
                    f"Deskripsi: {item.description}\n"
                    f"Habitat: Daerah Bogor\n"
                    f"Karakteristik: Tumbuhan khas Bogor\n"
                )
            elif type_name == 'fauna':
                # Khusus untuk fauna
                data['content'] = (
                    f"Fauna: {item.title}\n"
                    f"Deskripsi: {item.description}\n"
                    f"Habitat: Daerah Bogor\n"
                    f"Karakteristik: Hewan khas Bogor\n"
                )
            
            items.append(data)
        return items

    def get_context_data(self):
        all_data = {
            'destination': self._get_model_data(Destinations, 'destination'),
            'fauna': self._get_model_data(Fauna, 'fauna'),
            'flora': self._get_model_data(Flora, 'flora'),
            'health': self._get_model_data(Health, 'health'),
            'culinary': self._get_model_data(Kuliner, 'culinary')
        }
        
        context_parts = []
        for category, items in all_data.items():
            if items:
                context_parts.append(f"\n=== {category.upper()} ===")
                for item in items:
                    context_parts.append(item['content'])
        
        return "\n".join(context_parts), all_data

    def _get_friendly_response(self, response_type, *args):
        """Get random friendly response from templates"""
        template = random.choice(self.friendly_responses[response_type])
        return template.format(*args) if args else template

    def get_response(self, user_input, session_id):
        context_text, all_data = self.get_context_data()
        conversation_history = self._get_conversation_history(session_id)
        history_text = self._format_conversation_history(conversation_history)
        
        def clean_text(text):
            """Membersihkan HTML tags dari text"""
            clean = re.compile('<.*?>')
            return re.sub(clean, '', text)
        
        # Cek dulu apakah mencari item spesifik
        user_keywords = user_input.lower().split()
        found_specific_items = []
        for category, items in all_data.items():
            for item in items:
                # Cek apakah nama item ada dalam pertanyaan user
                if item['title'].lower() in user_input.lower():
                    found_specific_items.append({
                        'category': category,
                        'item': item
                    })
        
        # Jika menemukan item spesifik, berikan detail tentang item tersebut
        if found_specific_items:
            item = found_specific_items[0]['item']  # Ambil item pertama yang cocok
            category = found_specific_items[0]['category']
            
            response_text = (
                f"Aku punya informasi tentang {item['title']} nih! 😊\n\n"
                f"Detail:\n{clean_text(item['description'])}\n"
            )
            
            if 'location' in item:
                response_text += f"\nLokasi: {item['location']}"
            
            response_text += "\n\nAda yang ingin ditanyakan lagi? 😉"
            
            return {
                'text': response_text,
                'intent': category,
                'content_references': [{
                    'type': category,
                    'id': item['id'],
                    'name': item['title'],
                    'location': item.get('location', 'Bogor')
                }]
            }
        
        # Jika tidak menemukan item spesifik, lanjut ke pengecekan rekomendasi
        is_asking_recommendation = any(word in user_input.lower() 
                                     for word in ['rekomendasi', 'recommended', 'terbaik', 'paling enak', 'paling bagus'])
        
        if is_asking_recommendation:
            # Tentukan kategori yang diminta
            category = None
            if any(word in user_input.lower() for word in ['kuliner', 'makanan', 'makan']):
                category = 'culinary'
            elif any(word in user_input.lower() for word in ['wisata', 'destinasi']):
                category = 'destination'
            elif any(word in user_input.lower() for word in ['kesehatan', 'berobat']):
                category = 'health'
            
            if category and category in all_data:
                items = all_data[category]
                if items:
                    responses = []
                    category_name = {
                        'destination': 'destinasi wisata',
                        'culinary': 'kuliner',
                        'health': 'fasilitas kesehatan'
                    }.get(category, category)
                    
                    for item in items:
                        detail = f"- {item['title']}"
                        if 'location' in item:
                            detail += f" ({item['location']})"
                        detail += f"\n  {clean_text(item['description'])}"
                        responses.append(detail)
                    
                    response_text = (
                        f"Berikut rekomendasi {category_name} terbaik di Bogor nih! 😊\n\n"
                        f"{chr(10).join(responses)}\n\n"
                        f"Mau tau lebih detail tentang salah satunya? Tanya aja ya! 😉"
                    )
                    
                    return {
                        'text': response_text,
                        'intent': category,
                        'content_references': [{
                            'type': category,
                            'id': item['id'],
                            'name': item['title'],
                            'location': item.get('location', 'Bogor')
                        } for item in items]
                    }
        
        # Lanjutkan dengan logika normal jika bukan pertanyaan kategori
        try:
            prompt = f"""
            Kamu adalah Celya, asisten virtual yang ramah dan bersahabat untuk website ekowisata di daerah Bogor. 
            Gunakan bahasa yang santai, natural, dan mengalir seperti berbicara dengan teman.
            
            ATURAN PENTING (WAJIB DIPATUHI):
            1. HANYA berikan informasi tentang destinasi di daerah BOGOR
            2. HANYA berikan informasi yang ada dalam KONTEKS DATA yang diberikan
            3. JANGAN PERNAH membuat atau mengarang informasi di luar konteks
            4. Untuk informasi yang tidak tersedia, tawarkan alternatif yang ada di Bogor
            5. SELALU sertakan kata "Bogor" dalam setiap respons
            
            PANDUAN KHUSUS BERDASARKAN KATEGORI:
            1. Kuliner:
               - Sebutkan lokasi spesifik jika tersedia
               - Jelaskan karakteristik makanan
               - Kaitkan dengan budaya Bogor
               - Sebutkan Menu Dan Harga Jika Tersedia
               
            2. Kesehatan:
               - Sebutkan lokasi fasilitas kesehatan
               - Jelaskan layanan yang tersedia
               - Berikan informasi jam operasional jika ada
               
            3. Flora:
               - Sebutkan habitat spesifik di Bogor
               - Jelaskan karakteristik khusus
               - Kaitkan dengan ekosistem Bogor
               
            4. Fauna:
               - Sebutkan habitat alami di Bogor
               - Jelaskan karakteristik khusus
               - Kaitkan dengan konservasi di Bogor

        CONTOH RESPONS BERDASARKAN KATEGORI:
        1. Kuliner: "Di Bogor, kamu bisa mencoba [nama makanan] yang berlokasi di [lokasi]. Makanan ini terkenal dengan [karakteristik]..."
        2. Kesehatan: "Untuk layanan kesehatan di Bogor, tersedia [nama fasilitas] di [lokasi] yang menyediakan [layanan]..."
        3. Flora: "Di kawasan Bogor, tumbuh [nama flora] yang merupakan tumbuhan khas dengan [karakteristik]..."
        4. Fauna: "Di habitat alami Bogor, dapat ditemui [nama fauna] yang memiliki keunikan [karakteristik]..."
        
        PANDUAN KEPRIBADIAN:
        1. Ramah dan antusias dalam memberikan informasi
        2. Gunakan bahasa yang santai tapi tetap sopan
        3. Tunjukkan empati dan kepedulian
        4. Berikan semangat dan energi positif
        5. Ajak user untuk berinteraksi lebih lanjut
        6. Gunakan kata-kata yang mengajak seperti "yuk", "nih", "lho"
        7. Tambahkan emoji 😊😊😉🙂🐯🐱🐼 untuk membuat percakapan lebih hidup
        
        CONTOH RESPONS UNTUK INFORMASI TIDAK TERSEDIA:
        User: "Ceritakan tentang Taman Nasional Kutai"
        Response: "Maaf ya, aku fokus memberikan informasi seputar wisata di Bogor nih. Tapi kalau kamu tertarik, aku bisa ceritain tentang Kebun Raya Bogor yang nggak kalah keren! 😊"
        
        INSTRUKSI PENTING:
        1. Mulai dengan sapaan ramah "Hai! Saya Celya." HANYA untuk percakapan baru
        2. JANGAN gunakan sapaan "Hai! Saya Celya." untuk pertanyaan lanjutan
        3. Berikan informasi yang relevan dengan gaya bercerita yang menarik
        4. Untuk destinasi wisata, gambarkan dengan detail yang membuat orang tertarik
        5. Jika tidak ada informasi, WAJIB mulai dengan kata "Maaf"
        6. Berikan informasi yang relevan dengan gaya bercerita yang menarik
        7. Jika tidak ada informasi, berikan alternatif dari data yang tersedia
        8. Gunakan konteks percakapan untuk memberikan pengalaman yang personal
        9. WAJIB mulai dengan "Maaf" untuk informasi yang tidak tersedia
        10. Akhiri dengan ajakan untuk bertanya lebih lanjut
        
        CONTOH RESPONS YANG BAIK:
        Response: "Yuk, aku ceritain tentang destinasi wisata keren di Bogor aja! Di sini ada Kebun Raya Bogor yang nggak kalah menarik lho! 😊"
        
        RIWAYAT PERCAKAPAN:
        {history_text}
        
        KONTEKS DATA:
        {context_text}
        
        PERTANYAAN: {user_input}
        
        BERIKAN RESPONS DALAM FORMAT INI:
        RESPONSE: [jawaban lengkap dengan gaya bercerita yang menarik, HANYA dari data yang tersedia]
        TYPE: [destination/fauna/flora/guide/health/culinary]
        ITEMS: [daftar item yang disebutkan, HARUS ada dalam konteks data]
        
        PENANGANAN KHUSUS UNTUK PERTANYAAN DESTINASI:
        1. Jika user bertanya "destinasi apa saja di Bogor":
           - Berikan daftar lengkap destinasi yang tersedia
           - Sebutkan lokasi spesifik jika ada
           - Format: "Nama Destinasi (Lokasi)"
           - Akhiri dengan ajakan untuk bertanya lebih detail
        
        2. Jika user bertanya tentang destinasi spesifik:
           - Berikan informasi detail tentang destinasi tersebut
           - Sebutkan lokasi, karakteristik khusus, dan keunikan
           - Tambahkan rekomendasi destinasi terdekat jika ada
        
        CONTOH RESPONS DESTINASI:
        User: "Ada destinasi apa saja di Bogor?"
        Response: "Di Bogor ada banyak destinasi wisata menarik nih! 😊
        Berikut beberapa destinasi yang bisa kamu kunjungi:
        - Kebun Raya Bogor (Pusat Kota)
        - Taman Safari (Cisarua)
        - dst...
        
        Mau tau lebih detail tentang destinasi tertentu? Tanya aja ya! 😉"
        """

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response parts
            response_parts = {
                'text': '',
                'type': 'unknown',
                'items': []
            }
            
            current_section = None
            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('RESPONSE:'):
                    current_section = 'response'
                    response_parts['text'] = line.replace('RESPONSE:', '').strip()
                elif line.startswith('TYPE:'):
                    current_section = 'type'
                    response_parts['type'] = line.replace('TYPE:', '').strip().lower()
                elif line.startswith('ITEMS:'):
                    current_section = 'items'
                    items = line.replace('ITEMS:', '').strip()
                    response_parts['items'] = [item.strip() for item in items.split(',') if item.strip()]
                elif current_section == 'response' and line:
                    response_parts['text'] += ' ' + line

            # Validate that mentioned items exist in context
            valid_items = []
            if response_parts['type'] in all_data:
                available_titles = [item['title'].lower() for item in all_data[response_parts['type']]]
                for item in response_parts['items']:
                    if item.lower() in available_titles:
                        valid_items.append(item)
                    
            # Handle unknown topics or locations outside Bogor
            if "Kutai" in user_input or (not valid_items and response_parts['items']):
                response_parts['text'] = self._get_friendly_response('not_found', 
                    "informasi tentang lokasi di luar Bogor", 
                    "destinasi wisata di Bogor")
                response_parts['type'] = 'unknown'
                response_parts['items'] = []
                content_references = []
            else:
                # Find content references only for valid items
                content_references = []
                if response_parts['type'] in all_data and valid_items:
                    for item in all_data[response_parts['type']]:
                        if any(ref.lower() in item['title'].lower() for ref in valid_items):
                            ref_data = {
                                'type': response_parts['type'],
                                'id': item['id'],
                                'name': item['title']
                            }
                            if 'location' in item:
                                ref_data['location'] = item['location']
                            content_references.append(ref_data)

            # If no valid items found but we're asking about destinations in Bogor
            if not content_references and 'bogor' in user_input.lower() and 'wisata' in user_input.lower():
                # Add all Bogor destinations as references
                for item in all_data.get('destination', []):
                    if 'bogor' in item['title'].lower():
                        content_references.append({
                            'type': 'destination',
                            'id': item['id'],
                            'name': item['title']
                        })

            # Check if this is a new session or continuing conversation
            conversation_history = self._get_conversation_history(session_id)
            is_new_conversation = len(conversation_history) == 0

            # Add greeting only for new conversations
            if is_new_conversation and not response_parts['text'].startswith('Hai! Saya Celya'):
                greeting = self._get_friendly_response('greeting')
                response_parts['text'] = greeting + response_parts['text']
            elif not is_new_conversation:
                # Remove default greeting if it exists in continuing conversation
                if response_parts['text'].startswith('Hai! Saya Celya'):
                    response_parts['text'] = response_parts['text'].replace('Hai! Saya Celya.', '').strip()

            # Add follow-up question if not present
            if not any(phrase in response_parts['text'].lower() for phrase in ['ada yang ingin', 'mau tahu', 'ada lagi']):
                follow_up = self._get_friendly_response('follow_up')
                response_parts['text'] += f" {follow_up}"

            result = {
                'text': response_parts['text'],
                'intent': response_parts['type'],
                'content_references': content_references
            }
            
            self._update_conversation_history(session_id, user_input, result)
            return result

        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return {
                'text': self._get_friendly_response('not_found', 'informasi tersebut', 'hal-hal menarik'),
                'intent': 'error',
                'content_references': []
            } 