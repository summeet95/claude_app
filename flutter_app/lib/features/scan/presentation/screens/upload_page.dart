import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import '../providers/upload_provider.dart';

class UploadPage extends ConsumerStatefulWidget {
  const UploadPage({super.key, required this.videoPath});
  final String videoPath;

  @override
  ConsumerState<UploadPage> createState() => _UploadPageState();
}

class _UploadPageState extends ConsumerState<UploadPage> {
  @override
  void initState() {
    super.initState();
    // Start upload on first frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(uploadProvider.notifier).uploadVideo(widget.videoPath);
    });
  }

  @override
  Widget build(BuildContext context) {
    final uploadAsync = ref.watch(uploadProvider);

    ref.listen<AsyncValue<UploadState>>(uploadProvider, (_, next) {
      if (next.value?.phase == UploadPhase.done && next.value?.jobId != null) {
        context.pushReplacement('/results/${next.value!.jobId}');
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Uploading…')),
      body: uploadAsync.when(
        loading: () => const _UploadingView(progress: 0, label: 'Preparing…'),
        error: (e, _) => _ErrorView(
          message: e.toString(),
          onRetry: () => ref.read(uploadProvider.notifier).uploadVideo(widget.videoPath),
        ),
        data: (state) => switch (state.phase) {
          UploadPhase.idle || UploadPhase.creating => const _UploadingView(
              progress: 0,
              label: 'Creating job…',
            ),
          UploadPhase.uploading => _UploadingView(
              progress: state.uploadProgress,
              label: 'Uploading video (${(state.uploadProgress * 100).toStringAsFixed(0)}%)',
            ),
          UploadPhase.starting => const _UploadingView(
              progress: 1.0,
              label: 'Starting analysis…',
            ),
          UploadPhase.done => const _UploadingView(
              progress: 1.0,
              label: 'Done! Redirecting…',
            ),
          UploadPhase.error => _ErrorView(
              message: state.error ?? 'Unknown error',
              onRetry: () => ref.read(uploadProvider.notifier).uploadVideo(widget.videoPath),
            ),
        },
      ),
    );
  }
}

class _UploadingView extends StatelessWidget {
  const _UploadingView({required this.progress, required this.label});
  final double progress;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularPercentIndicator(
            radius: 80,
            lineWidth: 10,
            percent: progress.clamp(0.0, 1.0),
            center: Text(
              '${(progress * 100).toStringAsFixed(0)}%',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            progressColor: Theme.of(context).colorScheme.primary,
            backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
          ),
          const SizedBox(height: 24),
          Text(label, style: Theme.of(context).textTheme.bodyLarge),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            const Text('Upload failed', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
