import 'dart:convert';

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
    final List<dynamic> jobsJson =
        json['jobs'] as List<dynamic>? ?? [];

    return ChatApiResponse(
      userId: int.tryParse(json['user_id'].toString()) ?? 1,
      text: json['text']?.toString() ?? '',
      jobs: jobsJson
          .map(
            (dynamic job) => JobPosting.fromJson(
              job as Map<String, dynamic>,
            ),
          )
          .toList(),
    );
  }
}

class ChatApiService {
  static const String baseUrl = 'http://localhost:8000';

  /// 사용자 생성
  ///
  /// 이름 / 나이 / 전화번호 / 주소를 백엔드로 보내고
  /// 생성된 user_id를 반환받는다.
  Future<int> createUser({
    required String name,
    required int age,
    required String phone,
    required String address,
  }) async {
    final http.Response response = await http.post(
      Uri.parse('$baseUrl/users'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'name': name,
        'age': age,
        'phone': phone,
        'address': address,
      }),
    );

    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw Exception(
        '사용자 생성 실패: '
        '${response.statusCode}, body: ${response.body}',
      );
    }

    final Map<String, dynamic> decoded =
        jsonDecode(
          utf8.decode(response.bodyBytes),
        ) as Map<String, dynamic>;

    final int? userId =
        int.tryParse(decoded['user_id'].toString());

    if (userId == null) {
      throw Exception(
        '사용자 생성 실패: user_id가 없습니다.',
      );
    }

    return userId;
  }

  /// 채팅 메시지 전송
  Future<ChatApiResponse> sendMessage({
    required int userId,
    required String message,
  }) async {
    final http.Response response = await http.post(
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
        '챗봇 응답 실패: '
        '${response.statusCode}, body: ${response.body}',
      );
    }

    final Map<String, dynamic> decoded =
        jsonDecode(
          utf8.decode(response.bodyBytes),
        ) as Map<String, dynamic>;

    return ChatApiResponse.fromJson(decoded);
  }

  /// 조건 기반 일자리 추천
  Future<ChatApiResponse> recommendJobs({
    required int userId,
    required String jobType,
    required String region,
    bool? physicalLimit,
    String? workType,
    int? salaryMin,
  }) async {
    final http.Response response = await http.post(
      Uri.parse('$baseUrl/recommend'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'user_id': userId,
        'job_type': jobType,
        'region': region,
        'physical_limit': physicalLimit,
        'work_type': workType,
        'salary_min': salaryMin,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        '추천 응답 실패: '
        '${response.statusCode}, body: ${response.body}',
      );
    }

    final Map<String, dynamic> decoded =
        jsonDecode(
          utf8.decode(response.bodyBytes),
        ) as Map<String, dynamic>;

    final List<dynamic> jobsJson =
        decoded['jobs'] as List<dynamic>? ?? [];

    final List<JobPosting> jobs = jobsJson
        .map(
          (dynamic job) => JobPosting.fromJson(
            job as Map<String, dynamic>,
          ),
        )
        .toList();

    return ChatApiResponse(
      userId:
          int.tryParse(decoded['user_id'].toString()) ??
          userId,
      text: jobs.isEmpty
          ? '조건에 맞는 일자리를 찾지 못했습니다. '
              '다른 조건으로 다시 검색해볼까요?'
          : '총 ${jobs.length}개의 일자리를 찾았습니다. '
              '관심 있는 공고가 있으신가요?',
      jobs: jobs,
    );
  }

  /// 이미 본 공고를 제외하고 다른 공고 추천
  Future<ChatApiResponse> recommendMore({
    required int userId,
    List<String> excludeJobIds = const [],
  }) async {
    final http.Response response = await http.post(
      Uri.parse('$baseUrl/chat/recommend-more'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'user_id': userId,
        'exclude_job_ids': excludeJobIds,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        '추가 추천 실패: '
        '${response.statusCode}, body: ${response.body}',
      );
    }

    final Map<String, dynamic> decoded =
        jsonDecode(
          utf8.decode(response.bodyBytes),
        ) as Map<String, dynamic>;

    return ChatApiResponse.fromJson(decoded);
  }

  /// 지원하기 버튼 클릭 로그 저장
  Future<void> recordApplyClick({
    required int userId,
    required String jobId,
  }) async {
    final http.Response response = await http.post(
      Uri.parse('$baseUrl/job-clicks'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'user_id': userId,
        'job_id': jobId,
        'event_type': 'apply_click',
      }),
    );

    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw Exception(
        '지원하기 클릭 저장 실패: '
        '${response.statusCode}, body: ${response.body}',
      );
    }
  }
}