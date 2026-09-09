import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../models/chat_message.dart';
import '../models/chat_session.dart';
import '../services/chat_api_service.dart';

class ChatProvider extends ChangeNotifier {
  final ChatApiService chatApiService;
  final Uuid _uuid = const Uuid();

  ChatProvider({
    required this.chatApiService,
  }) {
    startNewChat();
  }

  // 백엔드에서 생성된 실제 사용자 ID
  int? _userId;
  int? get userId => _userId;

  // 초기 화면에서 입력받는 사용자 정보
  String? _userName;
  String? get userName => _userName;

  int? _userAge;
  int? get userAge => _userAge;

  String? _userPhone;
  String? get userPhone => _userPhone;

  String? _userAddress;
  String? get userAddress => _userAddress;

  bool get hasUserProfile {
    return _userId != null &&
        _userName != null &&
        _userAge != null &&
        _userPhone != null &&
        _userAddress != null;
  }

  final List<ChatSession> _sessions = [];

  List<ChatSession> get sessions {
    return List.unmodifiable(_sessions);
  }

  ChatSession? _currentSession;
  ChatSession? get currentSession => _currentSession;

  List<ChatMessage> get messages {
    return _currentSession?.messages ?? [];
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  /// 초기 사용자 정보 입력
  ///
  /// 입력받은 정보를 백엔드 /users API로 전송하고
  /// 반환된 실제 user_id를 저장한다.
  Future<void> setUserProfile({
    required String name,
    required int age,
    required String phone,
    required String address,
  }) async {
    if (_isLoading) {
      return;
    }

    _isLoading = true;
    notifyListeners();

    try {
      final int createdUserId =
          await chatApiService.createUser(
        name: name,
        age: age,
        phone: phone,
        address: address,
      );

      _userId = createdUserId;
      _userName = name;
      _userAge = age;
      _userPhone = phone;
      _userAddress = address;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 기존 사용자 ID 직접 설정이 필요한 경우 사용
  void setUserId(int id) {
    _userId = id;
    notifyListeners();
  }

  void startNewChat() {
    final ChatSession newSession = ChatSession(
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
    final ChatSession selected = _sessions.firstWhere(
      (ChatSession session) {
        return session.id == sessionId;
      },
    );

    _currentSession = selected;
    notifyListeners();
  }

  void showWelcomeMessage() {
    if (_currentSession == null) {
      return;
    }

    if (_currentSession!.messages.isNotEmpty) {
      return;
    }

    final String displayName = _userName ?? '사용자';

    _currentSession!.messages.add(
      ChatMessage(
        id: _uuid.v4(),
        sender: MessageSender.ai,
        type: MessageType.text,
        text: '$displayName님, 안녕하세요!\n'
            '어떤 일자리를 찾고 계신가요?\n'
            '원하시는 조건을 말씀해 주시면 맞는 공고를 찾아드릴게요.',
        createdAt: DateTime.now(),
      ),
    );

    notifyListeners();
  }

  /// 지원하기 버튼 클릭 로그 저장
  Future<void> recordApplyClick(
    String jobId,
  ) async {
    if (_userId == null) {
      return;
    }

    try {
      await chatApiService.recordApplyClick(
        userId: _userId!,
        jobId: jobId,
      );

      debugPrint(
        '지원하기 클릭 저장 완료 '
        '(userId=$_userId, jobId=$jobId)',
      );
    } catch (error) {
      debugPrint(
        '지원하기 클릭 저장 실패: $error',
      );
    }
  }

  Future<void> recommendMore(
    List<String> excludeJobIds,
  ) async {
    if (_userId == null ||
        _currentSession == null ||
        _isLoading) {
      return;
    }

    final ChatMessage loadingMessage = ChatMessage(
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

      _currentSession!.messages.removeWhere(
        (ChatMessage message) {
          return message.id == loadingMessage.id;
        },
      );

      _currentSession!.messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.text,
          text: response.text,
          createdAt: DateTime.now(),
        ),
      );

      if (response.jobs.isNotEmpty) {
        _currentSession!.messages.add(
          ChatMessage(
            id: _uuid.v4(),
            sender: MessageSender.ai,
            type: MessageType.jobRecommendation,
            text: '',
            jobs: response.jobs,
            createdAt: DateTime.now(),
          ),
        );
      }
    } catch (error) {
      _currentSession!.messages.removeWhere(
        (ChatMessage message) {
          return message.id == loadingMessage.id;
        },
      );

      _currentSession!.messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.text,
          text: '에러: $error',
          createdAt: DateTime.now(),
        ),
      );
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String text) async {
    final String trimmed = text.trim();

    if (trimmed.isEmpty ||
        _currentSession == null ||
        _isLoading) {
      return;
    }

    if (_userId == null) {
      return;
    }

    final ChatMessage userMessage = ChatMessage(
      id: _uuid.v4(),
      sender: MessageSender.user,
      type: MessageType.text,
      text: trimmed,
      createdAt: DateTime.now(),
    );

    _currentSession!.messages.add(userMessage);
    _updateCurrentSessionTitle(trimmed);

    final ChatMessage loadingMessage = ChatMessage(
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
        (ChatMessage message) {
          return message.id == loadingMessage.id;
        },
      );

      _currentSession!.messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.text,
          text: response.text,
          createdAt: DateTime.now(),
        ),
      );

      if (response.jobs.isNotEmpty) {
        _currentSession!.messages.add(
          ChatMessage(
            id: _uuid.v4(),
            sender: MessageSender.ai,
            type: MessageType.jobRecommendation,
            text: '',
            jobs: response.jobs,
            createdAt: DateTime.now(),
          ),
        );
      }
    } catch (error) {
      _currentSession!.messages.removeWhere(
        (ChatMessage message) {
          return message.id == loadingMessage.id;
        },
      );

      _currentSession!.messages.add(
        ChatMessage(
          id: _uuid.v4(),
          sender: MessageSender.ai,
          type: MessageType.text,
          text: '에러: $error',
          createdAt: DateTime.now(),
        ),
      );
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _updateCurrentSessionTitle(
    String firstMessage,
  ) {
    if (_currentSession == null) {
      return;
    }

    if (_currentSession!.title != '새 상담') {
      return;
    }

    final int index = _sessions.indexWhere(
      (ChatSession session) {
        return session.id == _currentSession!.id;
      },
    );

    if (index == -1) {
      return;
    }

    final String title = firstMessage.length > 12
        ? '${firstMessage.substring(0, 12)}...'
        : firstMessage;

    final ChatSession updatedSession = ChatSession(
      id: _currentSession!.id,
      title: title,
      messages: _currentSession!.messages,
      createdAt: _currentSession!.createdAt,
    );

    _sessions[index] = updatedSession;
    _currentSession = updatedSession;
  }
}