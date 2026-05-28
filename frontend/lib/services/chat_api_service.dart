import 'dart:convert';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

import '../models/job_posting.dart';

class ChatApiResponse {
  final int userId;
  final String text;
  final List<JobPosting> jobs;

  ChatApiResponse({
    required this.userId,
    required this.text,
    required this.jobs,
  });

  factory ChatApiResponse.fromJson(Map<String, dynamic> json) {
    final jobsJson = json['jobs'] as List<dynamic>? ?? [];

    return ChatApiResponse(
      userId: int.tryParse(json['user_id'].toString()) ?? 1,
      text: json['text'] ?? '',
      jobs: jobsJson
          .map((job) => JobPosting.fromJson(job as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ChatApiService {
  static String get baseUrl {
    if (kIsWeb) {
      // 웹에서는 같은 서버(상대 경로) 사용
      final origin = Uri.base.origin;
      return origin;
    }
    return 'http://localhost:8000';
  }

  Future<ChatApiResponse> recommendMore({
    required int userId,
    required List<String> excludeJobIds,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/recommend-more'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'exclude_job_ids': excludeJobIds,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('다른 공고 추천 실패: ${response.statusCode}');
    }

    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    return ChatApiResponse.fromJson(decoded);
  }

  Future<ChatApiResponse> sendMessage({
    required int userId,
    required String message,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'user_id': userId,
        'message': message,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        '챗봇 응답 실패: ${response.statusCode}, body: ${response.body}',
      );
    }

    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    return ChatApiResponse.fromJson(decoded);
  }
}
