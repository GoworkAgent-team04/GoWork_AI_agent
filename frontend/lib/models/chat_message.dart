import 'job_posting.dart';

enum MessageSender {
  user,
  ai,
}

enum MessageType {
  text,
  jobRecommendation,
  loading,
}

class ChatMessage {
  final String id;
  final MessageSender sender;
  final MessageType type;
  final String text;
  final List<JobPosting> jobs;
  final DateTime createdAt;

  ChatMessage({
    required this.id,
    required this.sender,
    required this.type,
    required this.text,
    this.jobs = const [],
    required this.createdAt,
  });
}