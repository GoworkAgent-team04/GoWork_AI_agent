import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'constants/app_colors.dart';
import 'providers/chat_provider.dart';
import 'screens/chat_screen.dart';

class SeniorJobApp extends StatelessWidget {
  const SeniorJobApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GoWork AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        scaffoldBackgroundColor: AppColors.background,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primary,
        ),
        fontFamily: 'Roboto',
        useMaterial3: true,
      ),
      home: const _StartupGate(),
    );
  }
}

/// 앱 시작 시 사용자 ID가 없으면 선택 화면을 보여줌
class _StartupGate extends StatelessWidget {
  const _StartupGate();

  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, _) {
        if (chatProvider.userId == null) {
          return const _UserSelectScreen();
        }
        return const ChatScreen();
      },
    );
  }
}

class _UserSelectScreen extends StatefulWidget {
  const _UserSelectScreen();

  @override
  State<_UserSelectScreen> createState() => _UserSelectScreenState();
}

class _UserSelectScreenState extends State<_UserSelectScreen> {
  final _controller = TextEditingController();
  String? _error;

  void _confirm() {
    final input = _controller.text.trim();
    final id = int.tryParse(input);
    if (id == null || id <= 0) {
      setState(() => _error = '올바른 숫자를 입력해 주세요');
      return;
    }
    context.read<ChatProvider>().setUserId(id);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Center(
        child: Container(
          width: 320,
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: AppColors.primary, width: 2),
            borderRadius: BorderRadius.circular(24),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'GoWork AI',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                '사용자 ID를 입력해 주세요',
                style: TextStyle(fontSize: 16, color: AppColors.textGrey),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _controller,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 20),
                decoration: InputDecoration(
                  hintText: '예: 1',
                  errorText: _error,
                  filled: true,
                  fillColor: AppColors.surface,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 14,
                  ),
                  border: OutlineInputBorder(
                    borderSide: BorderSide.none,
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                onSubmitted: (_) => _confirm(),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _confirm,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    '시작하기',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
