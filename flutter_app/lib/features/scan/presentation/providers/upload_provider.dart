import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/repositories/scan_repository.dart';

enum UploadPhase { idle, creating, uploading, starting, done, error }

class UploadState {
  const UploadState({
    this.phase = UploadPhase.idle,
    this.jobId,
    this.uploadProgress = 0.0,
    this.error,
  });

  final UploadPhase phase;
  final String? jobId;
  final double uploadProgress;
  final String? error;

  UploadState copyWith({
    UploadPhase? phase,
    String? jobId,
    double? uploadProgress,
    String? error,
  }) =>
      UploadState(
        phase: phase ?? this.phase,
        jobId: jobId ?? this.jobId,
        uploadProgress: uploadProgress ?? this.uploadProgress,
        error: error ?? this.error,
      );
}

class UploadNotifier extends AutoDisposeAsyncNotifier<UploadState> {
  @override
  Future<UploadState> build() async => const UploadState();

  Future<void> uploadVideo(
    String videoPath, {
    String? prefGender,
    String? prefLength,
    String? prefMaintenance,
  }) async {
    final repo = ref.read(scanRepositoryProvider);

    state = const AsyncValue.loading();

    try {
      // 1. Create job
      state = AsyncValue.data(const UploadState(phase: UploadPhase.creating));
      final (:jobId, :uploadUrl) = await repo.createJob(
        prefGender: prefGender,
        prefLength: prefLength,
        prefMaintenance: prefMaintenance,
      );

      // 2. Upload video
      state = AsyncValue.data(
        UploadState(phase: UploadPhase.uploading, jobId: jobId),
      );
      await repo.uploadVideo(
        uploadUrl,
        videoPath,
        onProgress: (sent, total) {
          final progress = total > 0 ? sent / total : 0.0;
          state = AsyncValue.data(
            UploadState(
              phase: UploadPhase.uploading,
              jobId: jobId,
              uploadProgress: progress,
            ),
          );
        },
      );

      // 3. Start job
      state = AsyncValue.data(
        UploadState(phase: UploadPhase.starting, jobId: jobId, uploadProgress: 1.0),
      );
      await repo.startJob(jobId);

      state = AsyncValue.data(
        UploadState(phase: UploadPhase.done, jobId: jobId, uploadProgress: 1.0),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

final uploadProvider =
    AsyncNotifierProvider.autoDispose<UploadNotifier, UploadState>(
  UploadNotifier.new,
);
