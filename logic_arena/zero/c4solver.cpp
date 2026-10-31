// Solveur exact de Puissance 4 (7 colonnes, 6 rangées) : négamax alpha-bêta, bitboards, table de transposition, ordre des coups.
// Les scores suivent la convention de Pascal Pons : > 0 si le joueur au trait gagne, < 0 s'il perd, 0 nul ; plus un gain est rapide, plus le score est grand.
// Position : `pos` = pierres du joueur au trait, `mask` = toutes les pierres ; bit d'une case = colonne * 7 + rangée (la 7e rangée est une sentinelle vide).
// Compilation : g++ -O2 -shared -o c4solver.dll c4solver.cpp
#include <cstdint>
#include <cstring>
#include <vector>
#include <algorithm>

namespace {
typedef uint64_t u64;
const int W = 7, H = 6;
const int MIN_SCORE = -(W * H) / 2 + 3;
const int MAX_SCORE = (W * H + 1) / 2 - 3;
const int ORDER[W] = {3, 2, 4, 1, 5, 0, 6};

constexpr u64 bottom_all() { u64 b = 0; for (int c = 0; c < W; c++) b |= (u64)1 << (c * (H + 1)); return b; }
const u64 BOTTOM = bottom_all();
const u64 BOARD = BOTTOM * (((u64)1 << H) - 1);
inline u64 col_mask(int c) { return (((u64)1 << H) - 1) << (c * (H + 1)); }

inline u64 winning_cells(u64 p, u64 mask) {
    u64 r = (p << 1) & (p << 2) & (p << 3);
    u64 q = (p << (H + 1)) & (p << 2 * (H + 1));
    r |= q & (p << 3 * (H + 1));
    r |= q & (p >> (H + 1));
    q = (p >> (H + 1)) & (p >> 2 * (H + 1));
    r |= q & (p << (H + 1));
    r |= q & (p >> 3 * (H + 1));
    q = (p << H) & (p << 2 * H);
    r |= q & (p << 3 * H);
    r |= q & (p >> H);
    q = (p >> H) & (p >> 2 * H);
    r |= q & (p << H);
    r |= q & (p >> 3 * H);
    q = (p << (H + 2)) & (p << 2 * (H + 2));
    r |= q & (p << 3 * (H + 2));
    r |= q & (p >> (H + 2));
    q = (p >> (H + 2)) & (p >> 2 * (H + 2));
    r |= q & (p << (H + 2));
    r |= q & (p >> 3 * (H + 2));
    return r & (BOARD ^ mask);
}

struct Position {
    u64 pos, mask;
    int moves;
    // clé canonique : la plus petite de la position et de son image miroir (colonnes inversées)
    inline u64 key() const {
        u64 a = pos + mask, b = 0;
        u64 q = pos, m = mask, mp = 0, mm = 0;
        for (int c = 0; c < W; c++) {
            u64 cm = ((u64)1 << (H + 1)) - 1;
            mp |= ((q >> (c * (H + 1))) & cm) << ((W - 1 - c) * (H + 1));
            mm |= ((m >> (c * (H + 1))) & cm) << ((W - 1 - c) * (H + 1));
        }
        b = mp + mm;
        return a < b ? a : b;
    }
    inline u64 possible() const { return (mask + BOTTOM) & BOARD; }
    inline void play(u64 m) { pos ^= mask; mask |= m; moves++; }
    inline bool can_win_next() const { return (winning_cells(pos, mask) & possible()) != 0; }
    inline u64 non_losing() const {
        u64 poss = possible();
        u64 opp = winning_cells(pos ^ mask, mask);
        u64 forced = poss & opp;
        if (forced) {
            if (forced & (forced - 1)) return 0;
            poss = forced;
        }
        return poss & ~(opp >> 1);
    }
    inline int move_score(u64 m) const { return __builtin_popcountll(winning_cells(pos | m, mask)); }
};

struct Table {
    std::vector<u64> keys;
    std::vector<int8_t> vals;
    size_t size;
    Table(size_t n = (1u << 23) + 9) : keys(n, 0), vals(n, 0), size(n) {}
    inline void put(u64 key, int8_t v) { size_t i = key % size; keys[i] = key; vals[i] = v; }
    inline int get(u64 key) const { size_t i = key % size; return keys[i] == key ? vals[i] : 0; }
    void clear() { std::fill(keys.begin(), keys.end(), 0); std::fill(vals.begin(), vals.end(), 0); }
};

Table* table = nullptr;
long long nodes = 0;

int negamax(const Position& P, int alpha, int beta) {
    nodes++;
    u64 possible = P.non_losing();
    if (possible == 0) return -(W * H - P.moves) / 2;
    if (P.moves >= W * H - 2) return 0;
    int mn = -(W * H - 2 - P.moves) / 2;
    if (alpha < mn) { alpha = mn; if (alpha >= beta) return alpha; }
    int mx = (W * H - 1 - P.moves) / 2;
    if (beta > mx) { beta = mx; if (alpha >= beta) return beta; }
    u64 key = P.key();
    if (int val = table->get(key)) {
        if (val > MAX_SCORE - MIN_SCORE + 1) {
            mn = val + 2 * MIN_SCORE - MAX_SCORE - 2;
            if (alpha < mn) { alpha = mn; if (alpha >= beta) return alpha; }
        } else {
            mx = val + MIN_SCORE - 1;
            if (beta > mx) { beta = mx; if (alpha >= beta) return beta; }
        }
    }
    // coups triés par nombre de menaces créées, à égalité par centralité
    u64 mv[W];
    int sc[W], n = 0;
    for (int i = W - 1; i >= 0; i--) {
        u64 m = possible & col_mask(ORDER[i]);
        if (m) {
            int s = P.move_score(m), j = n++;
            while (j > 0 && sc[j - 1] > s) { sc[j] = sc[j - 1]; mv[j] = mv[j - 1]; j--; }
            sc[j] = s; mv[j] = m;
        }
    }
    for (int i = n - 1; i >= 0; i--) {
        Position P2 = P;
        P2.play(mv[i]);
        int score = -negamax(P2, -beta, -alpha);
        if (score >= beta) { table->put(key, (int8_t)(score + MAX_SCORE - 2 * MIN_SCORE + 2)); return score; }
        if (score > alpha) alpha = score;
    }
    table->put(key, (int8_t)(alpha - MIN_SCORE + 1));
    return alpha;
}

int solve_position(const Position& P, bool weak) {
    if (P.can_win_next()) return (W * H + 1 - P.moves) / 2;
    int mn = -(W * H - P.moves) / 2, mx = (W * H + 1 - P.moves) / 2;
    if (weak) { mn = -1; mx = 1; }
    while (mn < mx) {
        int med = mn + (mx - mn) / 2;
        if (med <= 0 && mn / 2 < med) med = mn / 2;
        else if (med >= 0 && mx / 2 > med) med = mx / 2;
        int r = negamax(P, med, med + 1);
        if (r <= med) mx = r; else mn = r;
    }
    return mn;
}

// Recherche tactique à profondeur limitée : 1 si le joueur au trait gagne de force en au plus `depth` demi-coups, -1 s'il perd de force, 0 sinon.
int tactical(const Position& P, int depth) {
    if (P.moves == W * H) return 0;
    if (P.can_win_next()) return depth >= 1 ? 1 : 0;
    if (depth <= 1) return 0;
    u64 nl = P.non_losing();
    if (nl == 0) return -1;  // l'adversaire gagne au prochain coup quoi qu'on joue
    if (depth <= 2) return 0;
    bool all_lose = true;
    for (int i = 0; i < W; i++) {
        u64 m = nl & col_mask(ORDER[i]);
        if (!m) continue;
        Position Q = P;
        Q.play(m);
        int r = -tactical(Q, depth - 1);
        if (r == 1) return 1;
        if (r == 0) all_lose = false;
    }
    return all_lose ? -1 : 0;
}

inline Position make(u64 pos, u64 mask) { return Position{pos, mask, __builtin_popcountll(mask)}; }
}  // namespace

extern "C" {
void c4s_init() { if (!table) table = new Table(); }
void c4s_reset() { c4s_init(); table->clear(); nodes = 0; }
long long c4s_nodes() { return nodes; }

// Verdict tactique de chaque colonne (1 gain forcé, -1 perte forcée, 0 inconnu dans la limite de profondeur), point de vue du joueur au trait ; -1000 si pleine.
void c4s_tactical(u64 pos, u64 mask, int depth, int* out) {
    Position P = make(pos, mask);
    for (int c = 0; c < W; c++) {
        u64 m = (mask + ((u64)1 << (c * (H + 1)))) & col_mask(c);
        if (!(m & BOARD) || (mask & ((u64)1 << (c * (H + 1) + H - 1)))) { out[c] = -1000; continue; }
        if (winning_cells(pos, mask) & m) { out[c] = 1; continue; }
        Position Q = P;
        Q.play(m);
        out[c] = Q.moves == W * H ? 0 : -tactical(Q, depth - 1);
    }
}

// Score de la position pour le joueur au trait (weak = 1 : seulement le signe, plus rapide).
int c4s_solve(u64 pos, u64 mask, int weak) {
    c4s_init();
    return solve_position(make(pos, mask), weak != 0);
}

// Score de chaque colonne jouée (du point de vue du joueur au trait) ; -1000 pour une colonne pleine.
void c4s_scores(u64 pos, u64 mask, int weak, int* out) {
    c4s_init();
    Position P = make(pos, mask);
    for (int c = 0; c < W; c++) {
        u64 m = (mask + ((u64)1 << (c * (H + 1)))) & col_mask(c);
        if (!(m & BOARD) || (mask & ((u64)1 << (c * (H + 1) + H - 1)))) { out[c] = -1000; continue; }
        if (winning_cells(pos, mask) & m) { out[c] = (W * H + 1 - P.moves) / 2; continue; }
        Position Q = P;
        Q.play(m);
        if (Q.moves == W * H) { out[c] = 0; continue; }
        out[c] = -solve_position(Q, weak != 0);
    }
}
}
