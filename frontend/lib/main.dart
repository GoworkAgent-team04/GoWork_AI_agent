import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app.dart';
import 'providers/chat_provider.dart';
import 'services/chat_api_service.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ChatProvider(
            chatApiService: ChatApiService(),
          ),
        ),
      ],
      child: const SeniorJobApp(),
    ),
  );
}