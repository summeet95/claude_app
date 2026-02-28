import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/http/api_client.dart';
import '../models/job_model.dart';
import '../models/result_model.dart';

final scanApiProvider = Provider<ScanApi>(
  (ref) => ScanApi(ref.watch(apiClientProvider)),
);

class ScanApi {
  ScanApi(this._client);
  final ApiClient _client;

  /// POST /v1/jobs — returns {job_id, upload_url, upload_key, expires_in_seconds}
  Future<Map<String, dynamic>> createJob({
    String? prefGender,
    String? prefLength,
    String? prefMaintenance,
  }) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/v1/jobs',
      data: {
        if (prefGender != null) 'pref_gender': prefGender,
        if (prefLength != null) 'pref_length': prefLength,
        if (prefMaintenance != null) 'pref_maintenance': prefMaintenance,
      },
    );
    return response.data!;
  }

  /// POST /v1/jobs/{id}/start
  Future<void> startJob(String jobId) async {
    await _client.post('/v1/jobs/$jobId/start');
  }

  /// GET /v1/jobs/{id}
  Future<JobModel> getJobStatus(String jobId) async {
    final response = await _client.get<Map<String, dynamic>>('/v1/jobs/$jobId');
    return JobModel.fromJson(response.data!);
  }

  /// GET /v1/jobs/{id}/results
  Future<JobResults> getJobResults(String jobId) async {
    final response =
        await _client.get<Map<String, dynamic>>('/v1/jobs/$jobId/results');
    return JobResults.fromJson(response.data!);
  }

  /// Upload video to presigned PUT URL.
  Future<void> uploadVideo(
    String uploadUrl,
    String videoFilePath, {
    void Function(int sent, int total)? onProgress,
  }) =>
      _client.putToPresignedUrl(uploadUrl, videoFilePath, onProgress: onProgress);
}
