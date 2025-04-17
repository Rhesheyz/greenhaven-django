from rest_framework import serializers
from .models import Intents, Responses, InteractionLogs, ChatFeedback

class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responses
        fields = ['id', 'response']

class IntentSerializer(serializers.ModelSerializer):
    responses = ResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Intents
        fields = ['id', 'name', 'description', 'responses']

class InteractionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionLogs
        fields = ['id', 'user_input', 'intent', 'response', 'timestamp']

class ChatFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatFeedback
        fields = ['session_id', 'user_message', 'ai_response', 'rating', 'comment'] 