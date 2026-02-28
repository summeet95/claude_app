import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/job_model.dart';
import '../../data/models/result_model.dart';
import '../../data/repositories/scan_repository.dart';

class ResultsState {
  const ResultsState({
    this.job,
    this.results,
    this.isPolling = false,
    this.error,
  });

  final JobModel? job;
  final JobResults? results;
  final bool isPolling;
  final String? error;

  bool get isDone => results != null;
  bool get hasFailed => job?.status == JobStatus.failed;
}

class ResultsNotifier extends AutoDisposeAsyncNotifier<ResultsState> {
  Timer? _timer;

  @override
  Future<ResultsState> build() async => const ResultsState();

  Future<void> startPolling(String jobId) async {
    _timer?.cancel();
    final repo = ref.read(scanRepositoryProvider);

    state = AsyncValue.data(
      ResultsState(isPolling: true),
    );

    await _poll(repo, jobId);

    _timer = Timer.periodic(const Duration(seconds: 4), (_) async {
      if (state.value?.isDone == true || state.value?.hasFailed == true) {
        _timer?.cancel();
        return;
      }
      await _poll(repo, jobId);
    });
  }

  Future<void> _poll(ScanRepository repo, String jobId) async {
    try {
      final job = await repo.getStatus(jobId);
      if (job.status == JobStatus.completed) {
        final results = await repo.getResults(jobId);
        await repo.clearSavedJobId();
        state = AsyncValue.data(
          ResultsState(job: job, results: results, isPolling: false),
        );
        _timer?.cancel();
      } else if (job.status == JobStatus.failed) {
        state = AsyncValue.data(
          ResultsState(
            job: job,
            isPolling: false,
            error: job.errorMessage ?? 'Pipeline failed',
          ),
        );
        _timer?.cancel();
      } else {
        state = AsyncValue.data(
          ResultsState(job: job, isPolling: true),
        );
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}

final resultsProvider =
    AsyncNotifierProvider.autoDispose<ResultsNotifier, ResultsState>(
  ResultsNotifier.new,
);
