import 'package:flutter/foundation.dart';
import '../../../../core/config/env.dart';

@immutable
class BarberCard {
  const BarberCard({this.notes, this.guard, this.topLengthCm});

  final String? notes;
  final String? guard;
  final double? topLengthCm;

  factory BarberCard.fromJson(Map<String, dynamic> json) => BarberCard(
        notes: json['notes'] as String?,
        guard: json['guard'] as String?,
        topLengthCm: (json['top_length_cm'] as num?)?.toDouble(),
      );
}

@immutable
class StyleResult {
  const StyleResult({
    required this.rank,
    required this.styleId,
    required this.name,
    required this.slug,
    required this.score,
    required this.reasons,
    required this.texture,
    required this.length,
    required this.maintenance,
    required this.viewFront,
    required this.viewLeft,
    required this.viewRight,
    required this.viewBack,
    required this.barberCard,
  });

  final int rank;
  final String styleId;
  final String name;
  final String slug;
  final double score;
  final List<String> reasons;
  final String texture;
  final String length;
  final String maintenance;
  final String viewFront;
  final String viewLeft;
  final String viewRight;
  final String viewBack;
  final BarberCard barberCard;

  factory StyleResult.fromJson(Map<String, dynamic> json) => StyleResult(
        rank: json['rank'] as int,
        styleId: json['style_id'] as String,
        name: json['name'] as String,
        slug: json['slug'] as String,
        score: (json['score'] as num).toDouble(),
        reasons: (json['reasons'] as List).cast<String>(),
        texture: json['texture'] as String,
        length: json['length'] as String,
        maintenance: json['maintenance'] as String,
        viewFront: Env.rewriteMinioUrl(json['view_front'] as String),
        viewLeft: Env.rewriteMinioUrl(json['view_left'] as String),
        viewRight: Env.rewriteMinioUrl(json['view_right'] as String),
        viewBack: Env.rewriteMinioUrl(json['view_back'] as String),
        barberCard: BarberCard.fromJson(
          json['barber_card'] as Map<String, dynamic>,
        ),
      );
}

@immutable
class JobResults {
  const JobResults({
    required this.jobId,
    required this.headShape,
    required this.styles,
  });

  final String jobId;
  final String? headShape;
  final List<StyleResult> styles;

  factory JobResults.fromJson(Map<String, dynamic> json) => JobResults(
        jobId: json['job_id'] as String,
        headShape: json['head_shape'] as String?,
        styles: (json['styles'] as List)
            .map((s) => StyleResult.fromJson(s as Map<String, dynamic>))
            .toList(),
      );
}
