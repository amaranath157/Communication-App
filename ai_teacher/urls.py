from django.urls import path
from .controllers.teacher_controller import EvaluateTextView
from .controllers.grammar_controller import EnglishCorrectionView
from .controllers.listening_controller import ListeningGenerateView, ListeningEvaluateView

urlpatterns = [
    path('evaluate/', EvaluateTextView.as_view(), name='evaluate-text'),
    path('correct/',  EnglishCorrectionView.as_view(), name='english-correct'),
    path('listening/generate/', ListeningGenerateView.as_view(), name='listening-generate'),
    path('listening/evaluate/', ListeningEvaluateView.as_view(), name='listening-evaluate'),
]
