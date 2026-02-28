import 'dart:io' show File;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/env.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: Env.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
    _dio.interceptors.add(LogInterceptor(requestBody: false, responseBody: false));
  }

  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters}) =>
      _dio.get<T>(path, queryParameters: queryParameters);

  Future<Response<T>> post<T>(String path, {dynamic data}) =>
      _dio.post<T>(path, data: data);

  /// Upload a file directly to a presigned S3 PUT URL.
  Future<void> putToPresignedUrl(
    String url,
    String filePath, {
    void Function(int sent, int total)? onProgress,
  }) async {
    final fileBytes = await _readFile(filePath);
    await Dio().put(
      url,
      data: Stream.fromIterable([fileBytes]),
      options: Options(
        headers: {
          'Content-Type': 'video/mp4',
          'Content-Length': fileBytes.length,
        },
      ),
      onSendProgress: onProgress,
    );
  }

  Future<List<int>> _readFile(String path) async {
    final file = File(path);
    return file.readAsBytes();
  }
}
