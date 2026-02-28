import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'features/scan/presentation/screens/capture_page.dart';
import 'features/scan/presentation/screens/onboarding_page.dart';
import 'features/scan/presentation/screens/results_page.dart';
import 'features/scan/presentation/screens/upload_page.dart';

void main() {
  runApp(const ProviderScope(child: HairstyleApp()));
}

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (_, __) => const OnboardingPage(),
    ),
    GoRoute(
      path: '/capture',
      builder: (_, __) => const CapturePage(),
    ),
    GoRoute(
      path: '/upload',
      builder: (context, state) {
        final videoPath = state.extra as String;
        return UploadPage(videoPath: videoPath);
      },
    ),
    GoRoute(
      path: '/results/:jobId',
      builder: (context, state) {
        final jobId = state.pathParameters['jobId']!;
        return ResultsPage(jobId: jobId);
      },
    ),
  ],
);

class HairstyleApp extends StatelessWidget {
  const HairstyleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Hairstyle Try-On',
      theme: _buildTheme(Brightness.light),
      darkTheme: _buildTheme(Brightness.dark),
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }

  ThemeData _buildTheme(Brightness brightness) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6750A4),
      brightness: brightness,
    );
    return ThemeData(
      colorScheme: colorScheme,
      useMaterial3: true,
      appBarTheme: AppBarTheme(
        backgroundColor: colorScheme.surface,
        foregroundColor: colorScheme.onSurface,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardTheme(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }
}
