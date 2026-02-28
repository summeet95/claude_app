import 'package:flutter/foundation.dart';

abstract final class Env {
  /// Base URL for the FastAPI backend.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// MinIO public URL — rewritten for emulator in debug mode.
  static String get minioPublicUrl {
    const raw = String.fromEnvironment(
      'MINIO_PUBLIC_URL',
      defaultValue: 'http://10.0.2.2:9000',
    );
    return raw;
  }

  /// Rewrite MinIO container URL to host URL for emulator debug access.
  static String rewriteMinioUrl(String url) {
    if (!kDebugMode) return url;
    return url
        .replaceFirst('http://minio:9000', minioPublicUrl)
        .replaceFirst('http://localhost:9000', minioPublicUrl);
  }
}
