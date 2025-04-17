from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Intents, Responses, InteractionLogs
from .serializers import IntentSerializer, ResponseSerializer, InteractionLogSerializer, ChatFeedbackSerializer
from .services import GeminiService
import uuid

class ChatbotViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gemini_service = GeminiService()

    @action(detail=False, methods=['POST'])
    def chat(self, request):
        try:
            user_input = request.data.get('message')
            session_id = request.data.get('session_id')
            
            if not user_input:
                return Response(
                    {'error': 'Message is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate session_id if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            # Get response from Gemini
            response_data = self.gemini_service.get_response(user_input, session_id)

            return Response({
                'text': response_data['text'],
                'success': True,
                'intent': response_data['intent'],
                'content_references': response_data['content_references'],
                'session_id': session_id
            })

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['POST'])
    def feedback(self, request):
        try:
            serializer = ChatFeedbackSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Terima kasih atas feedback Anda! 😊'
                })
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
