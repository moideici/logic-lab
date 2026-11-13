// 2048 : professeur expectimax pour Garry Optimus (grille 64 bits, un quartet = log2 de la tuile,
// ligne r = bits 16r..16r+15, colonne c = bits 4c). Pas de limite a 2048 : une partie ne finit que bloquee.
// Compile a la demande (g++), appele par ctypes (logic_arena/t2048.py).
#include <cstdint>
#include <cmath>
#include <vector>
#include <thread>
#include <unordered_map>
#include <algorithm>
typedef uint64_t board_t;
typedef uint16_t row_t;
static row_t RL[65536], RR[65536];
static board_t CU[65536], CD[65536];
static float HEUR[65536];
static bool READY = false;
static const float LOST = 200000.f, MONO_W = 47.f, MERGE_W = 700.f, EMPTY_W = 270.f, SUM_W = 11.f;

static inline board_t transpose(board_t x) {
  board_t a1 = x & 0xF0F00F0FF0F00F0FULL, a2 = x & 0x0000F0F00000F0F0ULL, a3 = x & 0x0F0F00000F0F0000ULL;
  board_t a = a1 | (a2 << 12) | (a3 >> 12);
  board_t b1 = a & 0xFF00FF0000FF00FFULL, b2 = a & 0x00FF00FF00000000ULL, b3 = a & 0x00000000FF00FF00ULL;
  return b1 | (b2 >> 24) | (b3 << 24);
}
static inline board_t unpack_col(row_t r) { board_t t = r; return (t | (t << 12) | (t << 24) | (t << 36)) & 0x000F000F000F000FULL; }
static inline row_t reverse_row(row_t r) { return (row_t)((r >> 12) | ((r >> 4) & 0x00F0) | ((r << 4) & 0x0F00) | (r << 12)); }

static void init() {
  if (READY) return;
  for (unsigned row = 0; row < 65536; ++row) {
    unsigned line[4] = {(row >> 0) & 0xF, (row >> 4) & 0xF, (row >> 8) & 0xF, (row >> 12) & 0xF};
    float sum = 0;
    int empty = 0, merges = 0, prev = 0, counter = 0;
    for (int i = 0; i < 4; ++i) {
      int rank = line[i];
      sum += powf((float)rank, 3.5f);
      if (rank == 0) empty++;
      else {
        if (prev == rank) counter++;
        else if (counter > 0) { merges += 1 + counter; counter = 0; }
        prev = rank;
      }
    }
    if (counter > 0) merges += 1 + counter;
    float mono_l = 0, mono_r = 0;
    for (int i = 1; i < 4; ++i) {
      if (line[i - 1] > line[i]) mono_l += powf((float)line[i - 1], 4.f) - powf((float)line[i], 4.f);
      else mono_r += powf((float)line[i], 4.f) - powf((float)line[i - 1], 4.f);
    }
    HEUR[row] = LOST + EMPTY_W * empty + MERGE_W * merges - MONO_W * std::min(mono_l, mono_r) - SUM_W * sum;
    unsigned l2[4] = {line[0], line[1], line[2], line[3]};
    for (int i = 0; i < 3; ++i) {
      int j;
      for (j = i + 1; j < 4; ++j) if (l2[j] != 0) break;
      if (j == 4) break;
      if (l2[i] == 0) { l2[i] = l2[j]; l2[j] = 0; i--; }
      else if (l2[i] == l2[j]) { if (l2[i] != 15) l2[i]++; l2[j] = 0; }
    }
    RL[row] = (row_t)(l2[0] | (l2[1] << 4) | (l2[2] << 8) | (l2[3] << 12));
  }
  for (unsigned row = 0; row < 65536; ++row) {
    row_t rev = reverse_row((row_t)row);
    RR[row] = reverse_row(RL[rev]);
    CU[row] = unpack_col((row_t)row) ^ unpack_col(RL[row]);
    CD[row] = unpack_col((row_t)row) ^ unpack_col(RR[row]);
  }
  READY = true;
}

// 0 haut, 1 bas, 2 gauche, 3 droite
static inline board_t move(board_t b, int d) {
  board_t ret = b;
  if (d < 2) {
    board_t t = transpose(b);
    const board_t *T = d == 0 ? CU : CD;
    ret ^= T[(t >> 0) & 0xFFFF] << 0;
    ret ^= T[(t >> 16) & 0xFFFF] << 4;
    ret ^= T[(t >> 32) & 0xFFFF] << 8;
    ret ^= T[(t >> 48) & 0xFFFF] << 12;
  } else {
    const row_t *T = d == 2 ? RL : RR;
    for (int i = 0; i < 4; ++i) {
      board_t row = (b >> (16 * i)) & 0xFFFF;
      ret ^= (row ^ (board_t)T[row]) << (16 * i);
    }
  }
  return ret;
}
static inline float heur(board_t b) {
  board_t t = transpose(b);
  float s = 0;
  for (int i = 0; i < 4; ++i) { s += HEUR[(b >> (16 * i)) & 0xFFFF]; s += HEUR[(t >> (16 * i)) & 0xFFFF]; }
  return s;
}
static inline int count_empty(board_t x) {
  x |= (x >> 2) & 0x3333333333333333ULL;
  x |= (x >> 1);
  x = ~x & 0x1111111111111111ULL;
  return __builtin_popcountll(x);
}

struct State { int depth_limit; std::unordered_map<board_t, std::pair<float, int>> cache; };
static float chance(State &s, board_t b, float cprob, int curdepth);
static float maxn(State &s, board_t b, float cprob, int curdepth) {
  if (curdepth >= s.depth_limit) return heur(b);
  auto it = s.cache.find(b);
  if (it != s.cache.end() && it->second.second <= curdepth) return it->second.first;
  float best = 0;
  for (int d = 0; d < 4; ++d) {
    board_t nb = move(b, d);
    if (nb == b) continue;
    best = std::max(best, chance(s, nb, cprob, curdepth + 1));
  }
  s.cache[b] = {best, curdepth};
  return best;
}
static float chance(State &s, board_t b, float cprob, int curdepth) {
  if (cprob < 0.0001f) return heur(b);
  int ne = count_empty(b);
  if (ne == 0) return 0;
  cprob /= ne;
  float res = 0;
  board_t tmp = b, tile = 1;
  while (tile) {
    if ((tmp & 0xf) == 0) {
      res += maxn(s, b | tile, cprob * 0.9f, curdepth) * 0.9f;
      res += maxn(s, b | (tile << 1), cprob * 0.1f, curdepth) * 0.1f;
    }
    tmp >>= 4; tile <<= 4;
  }
  return res / ne;
}
static inline uint64_t xs(uint64_t &x) { x ^= x << 13; x ^= x >> 7; x ^= x << 17; return x; }
static board_t spawn(board_t nb, uint64_t &seed) {
  int ne = count_empty(nb);
  if (!ne) return nb;
  int k = (int)(xs(seed) % (uint64_t)ne);
  board_t tile = (xs(seed) % 10 == 0) ? 2 : 1, t = nb, pos = 1;
  int idx = 0;
  while (pos) {
    if ((t & 0xf) == 0) { if (idx == k) { nb |= tile * pos; break; } idx++; }
    t >>= 4; pos <<= 4;
  }
  return nb;
}

extern "C" {
// Valeurs des 4 coups (haut, bas, gauche, droite) ; -1e30 si illegal. depth = nombre de coups regardes.
void t_values(const board_t *boards, int n, int depth, float *out, int threads) {
  init();
  if (threads < 1) threads = 1;
  auto work = [&](int lo, int hi) {
    for (int i = lo; i < hi; ++i) {
      State s; s.depth_limit = depth * 2 - 1; board_t b = boards[i];
      for (int d = 0; d < 4; ++d) { board_t nb = move(b, d); out[i * 4 + d] = nb == b ? -1e30f : chance(s, nb, 1.f, 1); }
    }
  };
  std::vector<std::thread> th;
  int per = (n + threads - 1) / threads;
  for (int t = 0; t < threads; ++t) { int lo = t * per, hi = std::min(n, lo + per); if (lo < hi) th.emplace_back(work, lo, hi); }
  for (auto &t : th) t.join();
}
// Applique un coup par grille et fait apparaitre une tuile (aleatoire xorshift, seeds modifie).
void t_step(const board_t *boards, const int *dirs, int n, uint64_t *seeds, board_t *out) {
  init();
  for (int i = 0; i < n; ++i) {
    board_t nb = move(boards[i], dirs[i]);
    out[i] = nb != boards[i] ? spawn(nb, seeds[i]) : nb;
  }
}
void t_new(int n, uint64_t *seeds, board_t *out) {
  init();
  for (int i = 0; i < n; ++i) { if (!seeds[i]) seeds[i] = 88172645463325252ULL; board_t b = spawn(0, seeds[i]); out[i] = spawn(b, seeds[i]); }
}
void t_legal_batch(const board_t *boards, int n, int *out) { init(); for (int i = 0; i < n; ++i) { int m = 0; for (int d = 0; d < 4; ++d) if (move(boards[i], d) != boards[i]) m |= 1 << d; out[i] = m; } }
board_t t_move(board_t b, int d) { init(); return move(b, d); }
int t_legal_mask(board_t b) { init(); int m = 0; for (int d = 0; d < 4; ++d) if (move(b, d) != b) m |= 1 << d; return m; }
}
