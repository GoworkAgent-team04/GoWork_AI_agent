import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
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
        textTheme: GoogleFonts.notoSansKrTextTheme(),
        useMaterial3: true,
      ),
      home: const _StartupGate(),
    );
  }
}

/// 앱 시작 시 사용자 정보가 없으면 정보 입력 화면을 보여줌
class _StartupGate extends StatelessWidget {
  const _StartupGate();

  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, _) {
        if (!chatProvider.hasUserProfile) {
          return const _UserProfileScreen();
        }

        return const ChatScreen();
      },
    );
  }
}

class _UserProfileScreen extends StatefulWidget {
  const _UserProfileScreen();

  @override
  State<_UserProfileScreen> createState() =>
      _UserProfileScreenState();
}

class _UserProfileScreenState
    extends State<_UserProfileScreen> {
  final TextEditingController _nameController =
      TextEditingController();
  final TextEditingController _ageController =
      TextEditingController();
  final TextEditingController _phoneController =
      TextEditingController();
  final TextEditingController _addressController =
      TextEditingController();

  String? _error;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _nameController.dispose();
    _ageController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  Future<void> _confirm() async {
    if (_isSubmitting) {
      return;
    }

    final String name = _nameController.text.trim();
    final String ageText = _ageController.text.trim();
    final String phone = _phoneController.text.trim();
    final String address = _addressController.text.trim();

    final int? age = int.tryParse(ageText);

    if (name.isEmpty) {
      setState(() {
        _error = '이름을 입력해 주세요.';
      });
      return;
    }

    if (age == null || age <= 0 || age > 120) {
      setState(() {
        _error = '올바른 나이를 입력해 주세요.';
      });
      return;
    }

    if (phone.isEmpty) {
      setState(() {
        _error = '전화번호를 입력해 주세요.';
      });
      return;
    }

    if (address.isEmpty) {
      setState(() {
        _error = '주소를 입력해 주세요.';
      });
      return;
    }

    setState(() {
      _error = null;
      _isSubmitting = true;
    });

    try {
      await context.read<ChatProvider>().setUserProfile(
            name: name,
            age: age,
            phone: phone,
            address: address,
          );
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _error = '사용자 등록에 실패했습니다. 다시 시도해 주세요.';
      });

      debugPrint('사용자 생성 실패: $error');
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  InputDecoration _inputDecoration({
    required String label,
    required String hint,
  }) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      filled: true,
      fillColor: AppColors.surface,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: 18,
        vertical: 16,
      ),
      border: OutlineInputBorder(
        borderSide: BorderSide.none,
        borderRadius: BorderRadius.circular(16),
      ),
      enabledBorder: OutlineInputBorder(
        borderSide: BorderSide.none,
        borderRadius: BorderRadius.circular(16),
      ),
      focusedBorder: OutlineInputBorder(
        borderSide: const BorderSide(
          color: AppColors.primary,
          width: 2,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Container(
              width: 400,
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(
                  color: AppColors.primary,
                  width: 2,
                ),
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
                    '사용자 정보를 입력해 주세요',
                    style: TextStyle(
                      fontSize: 16,
                      color: AppColors.textGrey,
                    ),
                  ),
                  const SizedBox(height: 28),

                  TextField(
                    controller: _nameController,
                    textInputAction: TextInputAction.next,
                    decoration: _inputDecoration(
                      label: '이름',
                      hint: '예: 김순자',
                    ),
                  ),
                  const SizedBox(height: 14),

                  TextField(
                    controller: _ageController,
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.next,
                    decoration: _inputDecoration(
                      label: '나이',
                      hint: '예: 63',
                    ),
                  ),
                  const SizedBox(height: 14),

                  TextField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    textInputAction: TextInputAction.next,
                    decoration: _inputDecoration(
                      label: '전화번호',
                      hint: '예: 010-1234-5678',
                    ),
                  ),
                  const SizedBox(height: 14),

                  TextField(
                    controller: _addressController,
                    textInputAction: TextInputAction.done,
                    decoration: _inputDecoration(
                      label: '주소',
                      hint: '예: 서울 노원구 상계동',
                    ),
                    onSubmitted: (_) {
                      _confirm();
                    },
                  ),

                  if (_error != null) ...[
                    const SizedBox(height: 14),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        _error!,
                        style: const TextStyle(
                          color: Colors.red,
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],

                  const SizedBox(height: 24),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed:
                          _isSubmitting ? null : _confirm,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          vertical: 16,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(16),
                        ),
                      ),
                      child: _isSubmitting
                          ? const SizedBox(
                              width: 22,
                              height: 22,
                              child:
                                  CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Text(
                              '시작하기',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}