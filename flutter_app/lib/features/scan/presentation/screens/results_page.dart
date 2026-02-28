import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:percent_indicator/linear_percent_indicator.dart';
import 'package:shimmer/shimmer.dart';
import '../../data/models/job_model.dart';
import '../../data/models/result_model.dart';
import '../providers/results_provider.dart';

class ResultsPage extends ConsumerStatefulWidget {
  const ResultsPage({super.key, required this.jobId});
  final String jobId;

  @override
  ConsumerState<ResultsPage> createState() => _ResultsPageState();
}

class _ResultsPageState extends ConsumerState<ResultsPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(resultsProvider.notifier).startPolling(widget.jobId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final resultsAsync = ref.watch(resultsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Results'),
        actions: [
          TextButton.icon(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.refresh),
            label: const Text('New Scan'),
          ),
        ],
      ),
      body: resultsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _ErrorView(error: e.toString()),
        data: (state) {
          if (state.hasFailed) {
            return _ErrorView(error: state.error ?? 'Pipeline failed');
          }
          if (!state.isDone) {
            return _PollingView(job: state.job);
          }
          return _ResultsList(results: state.results!);
        },
      ),
    );
  }
}

// ── Polling progress view ─────────────────────────────────────────────────────

class _PollingView extends StatelessWidget {
  const _PollingView({this.job});
  final JobModel? job;

  @override
  Widget build(BuildContext context) {
    final progress = (job?.progress ?? 0) / 100.0;
    final status = job?.status.name ?? 'queued';

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 72,
              height: 72,
              child: CircularProgressIndicator(strokeWidth: 6),
            ),
            const SizedBox(height: 32),
            Text(
              _statusLabel(status),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            LinearPercentIndicator(
              percent: progress,
              lineHeight: 10,
              barRadius: const Radius.circular(5),
              progressColor: Theme.of(context).colorScheme.primary,
              backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
            ),
            const SizedBox(height: 8),
            Text(
              '${job?.progress ?? 0}%',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  String _statusLabel(String status) => switch (status) {
        'queued' => 'Queued — waiting for a worker…',
        'processing' => 'Analyzing your head shape…',
        _ => 'Processing…',
      };
}

// ── Results list ──────────────────────────────────────────────────────────────

class _ResultsList extends StatelessWidget {
  const _ResultsList({required this.results});
  final JobResults results;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Face Shape: ${results.headShape ?? 'Unknown'}',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text('${results.styles.length} recommended styles',
                    style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ),
        SliverList.builder(
          itemCount: results.styles.length,
          itemBuilder: (_, i) => _StyleCard(style: results.styles[i]),
        ),
        const SliverPadding(padding: EdgeInsets.only(bottom: 32)),
      ],
    );
  }
}

// ── Style card ────────────────────────────────────────────────────────────────

class _StyleCard extends StatefulWidget {
  const _StyleCard({required this.style});
  final StyleResult style;

  @override
  State<_StyleCard> createState() => _StyleCardState();
}

class _StyleCardState extends State<_StyleCard> {
  int _selectedView = 0;
  final _views = ['front', 'left', 'right', 'back'];

  List<String> get _viewUrls => [
        widget.style.viewFront,
        widget.style.viewLeft,
        widget.style.viewRight,
        widget.style.viewBack,
      ];

  @override
  Widget build(BuildContext context) {
    final style = widget.style;
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          ListTile(
            leading: CircleAvatar(
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Text(
                '#${style.rank}',
                style: TextStyle(
                  color: theme.colorScheme.onPrimaryContainer,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            title: Text(style.name, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(
              '${style.length} • ${style.texture} • ${style.maintenance} maintenance',
            ),
            trailing: _ScoreBadge(score: style.score),
          ),

          // 4-View image carousel
          AspectRatio(
            aspectRatio: 1,
            child: ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.zero),
              child: Stack(
                children: [
                  CachedNetworkImage(
                    imageUrl: _viewUrls[_selectedView],
                    fit: BoxFit.cover,
                    width: double.infinity,
                    placeholder: (_, __) => Shimmer.fromColors(
                      baseColor: Colors.grey[300]!,
                      highlightColor: Colors.grey[100]!,
                      child: Container(color: Colors.white),
                    ),
                    errorWidget: (_, __, ___) => Container(
                      color: theme.colorScheme.surfaceVariant,
                      child: const Icon(Icons.image_not_supported, size: 48),
                    ),
                  ),
                  // View selector tabs
                  Positioned(
                    bottom: 8,
                    left: 0,
                    right: 0,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(
                        4,
                        (i) => GestureDetector(
                          onTap: () => setState(() => _selectedView = i),
                          child: Container(
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: _selectedView == i
                                  ? theme.colorScheme.primary
                                  : Colors.black45,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              _views[i],
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 11,
                                fontWeight: _selectedView == i
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Reasons
          if (style.reasons.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: style.reasons
                    .map((r) => Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.check_circle_outline,
                                size: 16, color: theme.colorScheme.primary),
                            const SizedBox(width: 6),
                            Expanded(child: Text(r, style: theme.textTheme.bodySmall)),
                          ],
                        ))
                    .toList(),
              ),
            ),

          // Barber card
          _BarberCardTile(card: style.barberCard),
        ],
      ),
    );
  }
}

class _ScoreBadge extends StatelessWidget {
  const _ScoreBadge({required this.score});
  final double score;

  @override
  Widget build(BuildContext context) {
    final pct = (score * 100).toStringAsFixed(0);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        '$pct%',
        style: TextStyle(
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.onSecondaryContainer,
        ),
      ),
    );
  }
}

class _BarberCardTile extends StatefulWidget {
  const _BarberCardTile({required this.card});
  final BarberCard card;

  @override
  State<_BarberCardTile> createState() => _BarberCardTileState();
}

class _BarberCardTileState extends State<_BarberCardTile> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final card = widget.card;
    if (card.notes == null && card.guard == null && card.topLengthCm == null) {
      return const SizedBox.shrink();
    }

    return ExpansionTile(
      leading: const Icon(Icons.content_cut_rounded),
      title: const Text('Barber Instructions'),
      initiallyExpanded: false,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (card.guard != null)
                _InfoRow(label: 'Guard / Clipper', value: card.guard!),
              if (card.topLengthCm != null)
                _InfoRow(label: 'Top length', value: '${card.topLengthCm} cm'),
              if (card.notes != null) ...[
                const SizedBox(height: 8),
                Text(card.notes!, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.w600)),
          Text(value),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error});
  final String error;

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
            const Text('Something went wrong',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(error, textAlign: TextAlign.center),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => context.go('/'),
              icon: const Icon(Icons.home),
              label: const Text('Start Over'),
            ),
          ],
        ),
      ),
    );
  }
}
