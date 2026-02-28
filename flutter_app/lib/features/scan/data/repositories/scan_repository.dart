import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/job_model.dart';
import '../models/result_model.dart';
import '../sources/scan_api.dart';

const _kJobIdKey = 'active_job_id';

final scanRepositoryProvider = Provider<ScanRepository>(
  (ref) => ScanRepository(ref.watch(scanApiProvider)),
);

class ScanRepository {
  ScanRepository(this._api);

  final ScanApi _api;
  final _storage = const FlutterSecureStorage();

  /// Create a new job and persist jobId for resume after app kill.
  Future<({String jobId, String uploadUrl})> createJob({
    String? prefGender,
    String? prefLength,
    String? prefMaintenance,
  }) async {
    final data = await _api.createJob(
      prefGender: prefGender,
      prefLength: prefLength,
      prefMaintenance: prefMaintenance,
    );
    final jobId = data['job_id'] as String;
    final uploadUrl = data['upload_url'] as String;
    await _storage.write(key: _kJobIdKey, value: jobId);
    return (jobId: jobId, uploadUrl: uploadUrl);
  }

  /// Upload video directly to presigned S3 URL.
  Future<void> uploadVideo(
    String uploadUrl,
    String videoPath, {
    void Function(int sent, int total)? onProgress,
  }) =>
      _api.uploadVideo(uploadUrl, videoPath, onProgress: onProgress);

  /// Start the ML pipeline for a job.
  Future<void> startJob(String jobId) => _api.startJob(jobId);

  /// Poll job status.
  Future<JobModel> getStatus(String jobId) => _api.getJobStatus(jobId);

  /// Fetch final results.
  Future<JobResults> getResults(String jobId) => _api.getJobResults(jobId);

  /// Retrieve persisted jobId (resume after kill).
  Future<String?> getSavedJobId() => _storage.read(key: _kJobIdKey);

  /// Clear persisted jobId when done.
  Future<void> clearSavedJobId() => _storage.delete(key: _kJobIdKey);
}
