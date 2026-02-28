import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';

class CapturePage extends StatefulWidget {
  const CapturePage({super.key});

  @override
  State<CapturePage> createState() => _CapturePageState();
}

class _CapturePageState extends State<CapturePage> with WidgetsBindingObserver {
  CameraController? _controller;
  bool _isRecording = false;
  bool _permissionDenied = false;
  String? _videoPath;
  int _recordingSeconds = 0;
  static const _maxSeconds = 15;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initCamera();
  }

  Future<void> _initCamera() async {
    final status = await Permission.camera.request();
    await Permission.microphone.request();
    if (!status.isGranted) {
      setState(() => _permissionDenied = true);
      return;
    }

    final cameras = await availableCameras();
    final front = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );

    _controller = CameraController(
      front,
      ResolutionPreset.high,
      enableAudio: false,
    );
    await _controller!.initialize();
    if (mounted) setState(() {});
  }

  Future<void> _startRecording() async {
    if (_controller == null || !_controller!.value.isInitialized) return;
    await _controller!.startVideoRecording();
    setState(() {
      _isRecording = true;
      _recordingSeconds = 0;
    });
    _tick();
  }

  void _tick() {
    Future.delayed(const Duration(seconds: 1), () {
      if (!mounted || !_isRecording) return;
      setState(() => _recordingSeconds++);
      if (_recordingSeconds >= _maxSeconds) {
        _stopRecording();
      } else {
        _tick();
      }
    });
  }

  Future<void> _stopRecording() async {
    if (_controller == null || !_isRecording) return;
    final file = await _controller!.stopVideoRecording();
    setState(() {
      _isRecording = false;
      _videoPath = file.path;
    });
  }

  void _proceed() {
    if (_videoPath == null) return;
    context.push('/upload', extra: _videoPath);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_permissionDenied) {
      return _PermissionDeniedView(onSettings: () => openAppSettings());
    }

    if (_controller == null || !_controller!.value.isInitialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera preview
          Positioned.fill(child: CameraPreview(_controller!)),

          // Head silhouette guide (CustomPainter)
          Positioned.fill(child: CustomPaint(painter: _SilhouettePainter())),

          // Top bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white),
                    onPressed: () => context.pop(),
                  ),
                  const Spacer(),
                  if (_isRecording)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.red,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '${_maxSeconds - _recordingSeconds}s',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ),
                ],
              ),
            ),
          ),

          // Bottom controls
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  children: [
                    Text(
                      _videoPath != null
                          ? 'Video ready!'
                          : _isRecording
                              ? 'Slowly rotate your head'
                              : 'Tap to start recording',
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_videoPath != null) ...[
                          OutlinedButton.icon(
                            onPressed: () => setState(() => _videoPath = null),
                            icon: const Icon(Icons.replay, color: Colors.white),
                            label: const Text('Retake', style: TextStyle(color: Colors.white)),
                            style: OutlinedButton.styleFrom(
                              side: const BorderSide(color: Colors.white),
                            ),
                          ),
                          const SizedBox(width: 16),
                          FilledButton.icon(
                            onPressed: _proceed,
                            icon: const Icon(Icons.check),
                            label: const Text('Use Video'),
                          ),
                        ] else
                          GestureDetector(
                            onTap: _isRecording ? _stopRecording : _startRecording,
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 200),
                              width: 72,
                              height: 72,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _isRecording ? Colors.red : Colors.white,
                                border: Border.all(color: Colors.white, width: 4),
                              ),
                              child: Icon(
                                _isRecording ? Icons.stop : Icons.fiber_manual_record,
                                color: _isRecording ? Colors.white : Colors.red,
                                size: 36,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SilhouettePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height * 0.42;
    final rx = size.width * 0.28;
    final ry = size.height * 0.32;

    final paint = Paint()
      ..color = Colors.white.withOpacity(0.35)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    canvas.drawOval(Rect.fromCenter(center: Offset(cx, cy), width: rx * 2, height: ry * 2), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _PermissionDeniedView extends StatelessWidget {
  const _PermissionDeniedView({required this.onSettings});
  final VoidCallback onSettings;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.videocam_off, size: 64),
              const SizedBox(height: 16),
              const Text('Camera permission required',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('Please grant camera access in settings.'),
              const SizedBox(height: 24),
              FilledButton(onPressed: onSettings, child: const Text('Open Settings')),
            ],
          ),
        ),
      ),
    );
  }
}
