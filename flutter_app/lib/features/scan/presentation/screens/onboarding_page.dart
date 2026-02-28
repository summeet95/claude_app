import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class OnboardingPage extends StatelessWidget {
  const OnboardingPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 48),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              Icon(
                Icons.content_cut_rounded,
                size: 96,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(height: 32),
              Text(
                'Find Your\nPerfect Hairstyle',
                textAlign: TextAlign.center,
                style: theme.textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Record a short 360° video of your head.\nOur AI analyzes your face shape and recommends the best styles — with barber instructions.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
              const Spacer(),
              _FeatureRow(icon: Icons.videocam_rounded, text: '10-second head scan'),
              const SizedBox(height: 12),
              _FeatureRow(
                icon: Icons.psychology_rounded,
                text: 'AI face-shape analysis',
              ),
              const SizedBox(height: 12),
              _FeatureRow(
                icon: Icons.auto_awesome_rounded,
                text: 'Top 10 personalized styles',
              ),
              const SizedBox(height: 12),
              _FeatureRow(
                icon: Icons.content_paste_rounded,
                text: 'Barber-ready instructions',
              ),
              const Spacer(flex: 2),
              FilledButton.icon(
                onPressed: () => context.push('/capture'),
                icon: const Icon(Icons.camera_alt_rounded),
                label: const Text('Start Scan'),
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(56),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeatureRow extends StatelessWidget {
  const _FeatureRow({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 12),
        Text(text, style: Theme.of(context).textTheme.bodyLarge),
      ],
    );
  }
}
