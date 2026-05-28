import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../models/chat_message.dart';
import '../models/chat_session.dart';
import '../services/chat_api_service.dart';

class ChatProvider extends ChangeNotifier {
  final ChatApiService chatApiService;
  final Uuid _uuid = const Uuid();

  int? _userId;
  int? get userId => _userId;

  ChatProvider({
    required this.chatApiService,
  }) {
    startNewChat();
  }

  void setUserId(int id) {
    _userId = id;
    notifyListeners();
  }

  final List<ChatSession> _sessions = [];
  List<ChatSession> get sessions => List.unmodifiable(_sessions);

  ChatSession? _currentSession;
  ChatSession? get currentSession => _currentSession;

  List<ChatMessage> get messages => _currentSession?.messages ?? [];

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  void startNewChat() {
    final newSession = ChatSession(
      id: _uuid.v4(),
      title: '새 상담',
      messages: [],
      createdAt: DateTime.now(),
    );

    _currentSession = newSession;
    _sessions.insert(0, newSession);

    notifyListeners();
  }

  void openSession(String sessionId) {
    final selected = _sessions.firstWhere(
      (session) => session.id == sessionId,
    );

    _currentSession = selected;
    notifyListeners();
  }

  void showWelcomeMessage() {
    if (_currentSession == null) return;
    _currentSession!.messages.add(ChatMessage(
      id: _uuid.v4(),
      sender: MessageSender.ai,
      type: MessageType.text,
      text: '안녕하세요! 어떤 일자리를 찾고 계신가요?\n원하시는 조건을 말씀해 주시면 맞는 공고를 찾아드릴게요.',
      createdAt: DateTime.now(),
    ));
    notifyListeners();
  }

  Future<void> recommendMore(List<String> excludeJobIds) async {
    if (_userId == null || _currentSession == null || _isLoading) return;

    final loadingMessage = ChatMessage(
      id: _uuid.v4(),
      sender: MessageSender.ai,
      type: MessageType.loading,
      text: '',
      createdAt: DateTime.now(),
    );

    _currentSession!.messages.add(loadingMessage);
    _isLoading = true;
    notifyListeners();

    try {
      final response = await chatApiService.recommendMore(
        userId: _userId!,
        excludeJobIds: excludeJobIds,
      );

      _currentSession!.messages.removeWhere((m) => m.id == loadingMessage.id);

      _currentSession!.messages.add(ChatMessage(
        id: _uuid.v4(),
        sender: MessageSender.ai,
        type: MessageType.text,
        text: response.text,
        createdAt: DateTime.now(),
      ));

      if (response.jobs.isNotEmpty) {
        _currentSession!.messages.add(ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.jobRecommendation,
          text: '',
          jobs: response.jobs,
          createdAt: DateTime.now(),
        ));
      }
    } catch (e) {
      _currentSession!.messages.removeWhere((m) => m.id == loadingMessage.id);
      _currentSession!.messages.add(ChatMessage(
        id: _uuid.v4(),
        sender: MessageSender.ai,
        type: MessageType.text,
        text: '에러: $e',
        createdAt: DateTime.now(),
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _currentSession == null || _isLoading) return;
    if (_userId == null) return;

    final userMessage = ChatMessage(
      id: _uuid.v4(),
      sender: MessageSender.user,
      type: MessageType.text,
      text: trimmed,
      createdAt: DateTime.now(),
    );

    _currentSession!.messages.add(userMessage);
    _updateCurrentSessionTitle(trimmed);

    final loadingMessage = ChatMessage(
      id: _uuid.v4(),
      sender: MessageSender.ai,
      type: MessageType.loading,
      text: '',
      createdAt: DateTime.now(),
    );

    _currentSession!.messages.add(loadingMessage);
    _isLoading = true;
    notifyListeners();

    try {
      final response = await chatApiService.sendMessage(
        userId: _userId!,
        message: trimmed,
      );

      _currentSession!.messages.removeWhere(
        (message) => message.id == loadingMessage.id,
      );

      // 텍스트 응답 먼저 표시
      _currentSession!.messages.add(ChatMessage(
        id: _uuid.v4(),
        sender: MessageSender.ai,
        type: MessageType.text,
        text: response.text,
        createdAt: DateTime.now(),
      ));

      // 공고가 있으면 바로 카드 표시
      if (response.jobs.isNotEmpty) {
        _currentSession!.messages.add(ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.jobRecommendation,
          text: '',
          jobs: response.jobs,
          createdAt: DateTime.now(),
        ));
      }
    } catch (e) {
      _currentSession!.messages.removeWhere(
        (message) => message.id == loadingMessage.id,
      );

      _currentSession!.messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.text,
          text: '에러: $e',
          createdAt: DateTime.now(),
        ),
      );
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _updateCurrentSessionTitle(String firstMessage) {
    if (_currentSession == null) return;
    if (_currentSession!.title != '새 상담') return;

    final index = _sessions.indexWhere(
      (session) => session.id == _currentSession!.id,
    );

    if (index == -1) return;

    final title = firstMessage.length > 12
        ? '${firstMessage.substring(0, 12)}...'
        : firstMessage;

    final updated = ChatSession(
      id: _currentSession!.id,
      title: title,
      messages: _currentSession!.messages,
      createdAt: _currentSession!.createdAt,
    );

    _sessions[index] = updated;
    _currentSession = updated;
  }
}
