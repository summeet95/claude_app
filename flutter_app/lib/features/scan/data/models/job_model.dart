import 'package:flutter/foundation.dart';

enum JobStatus {
  pending,
  queued,
  processing,
  completed,
  failed;

  static JobStatus fromString(String s) =>
      JobStatus.values.firstWhere((e) => e.name == s, orElse: () => JobStatus.pending);

  bool get isTerminal => this == completed || this == failed;
  bool get isInProgress => this == queued || this == processing;
}

@immutable
class JobModel {
  const JobModel({
    required this.jobId,
    required this.status,
    required this.progress,
    this.errorMessage,
    this.headShape,
  });

  final String jobId;
  final JobStatus status;
  final int progress;
  final String? errorMessage;
  final String? headShape;

  factory JobModel.fromJson(Map<String, dynamic> json) => JobModel(
        jobId: json['job_id'] as String,
        status: JobStatus.fromString(json['status'] as String),
        progress: json['progress'] as int? ?? 0,
        errorMessage: json['error_message'] as String?,
        headShape: json['head_shape'] as String?,
      );

  JobModel copyWith({
    JobStatus? status,
    int? progress,
    String? errorMessage,
    String? headShape,
  }) =>
      JobModel(
        jobId: jobId,
        status: status ?? this.status,
        progress: progress ?? this.progress,
        errorMessage: errorMessage ?? this.errorMessage,
        headShape: headShape ?? this.headShape,
      );
}
