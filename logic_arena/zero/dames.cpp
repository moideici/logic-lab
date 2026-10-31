// Dames de multi (packages/engines/src/games/dames) : génération des coups identique au moteur TypeScript, pour l'entraînement de Garry.
// Cases 0..63 (rangée * 8 + colonne), jouables si (rangée + colonne) est impair. Pièces : 0 vide, 1 pion du joueur 0 (monte), 2 dame du joueur 0,
// 3 pion du joueur 1 (descend), 4 dame du joueur 1. Prise obligatoire, rafle maximale, dames volantes, victimes retirées en fin de rafle.
// Compilation : g++ -O2 -static -shared -o dames.dll dames.cpp
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <cmath>

namespace {
typedef int8_t i8;
const int MAXMOVES = 256, REC = 72;  // enregistrement d'un coup : [longueur du chemin, nb de prises, chemin (33), prises (32), pad]
const int DR[4] = {-1, -1, 1, 1}, DC[4] = {-1, 1, -1, 1};

inline int owner(int p) { return p == 0 ? -1 : p <= 2 ? 0 : 1; }
inline bool is_king(int p) { return p == 2 || p == 4; }
inline int crown(int p, int cell) { return (p == 1 && cell < 8) ? 2 : (p == 3 && cell >= 56) ? 4 : p; }
inline int stepc(int cell, int dr, int dc) {
    int r = cell / 8 + dr, c = cell % 8 + dc;
    return (r >= 0 && r < 8 && c >= 0 && c < 8) ? r * 8 + c : -1;
}

struct Gen {
    i8 board[64];
    int seat;
    int count = 0;
    int max_caps = 0;
    i8 out[MAXMOVES * REC];

    void push(const int* path, int plen, const int* caps, int ncaps) {
        if (count >= MAXMOVES) return;
        i8* rec = out + count * REC;
        std::memset(rec, 0, REC);
        rec[0] = (i8)plen;
        rec[1] = (i8)ncaps;
        for (int i = 0; i < plen; i++) rec[2 + i] = (i8)path[i];
        for (int i = 0; i < ncaps; i++) rec[35 + i] = (i8)caps[i];
        count++;
    }

    void visit(int at, int piece, int* path, int plen, int* taken, int ntaken) {
        bool continued = false;
        for (int d = 0; d < 4; d++) {
            int target = stepc(at, DR[d], DC[d]);
            if (is_king(piece)) while (target >= 0 && board[target] == 0) target = stepc(target, DR[d], DC[d]);
            if (target < 0 || owner(board[target]) != 1 - seat) continue;
            bool already = false;
            for (int i = 0; i < ntaken; i++) if (taken[i] == target) already = true;
            if (already) continue;
            int to = stepc(target, DR[d], DC[d]);
            while (to >= 0 && board[to] == 0) {
                continued = true;
                board[at] = 0;
                int promoted = crown(piece, to);
                board[to] = (i8)promoted;
                path[plen] = to;
                taken[ntaken] = target;
                visit(to, promoted, path, plen + 1, taken, ntaken + 1);
                board[to] = 0;
                board[at] = (i8)piece;
                if (!is_king(piece)) break;
                to = stepc(to, DR[d], DC[d]);
            }
        }
        if (!continued && ntaken > 0) {
            push(path, plen, taken, ntaken);
        }
    }
};
}  // namespace

extern "C" {
// Écrit les coups légaux de `seat` dans `out` (enregistrements de 72 octets) ; renvoie leur nombre.
int dames_moves(const i8* cells, int seat, i8* out) {
    Gen g;
    std::memcpy(g.board, cells, 64);
    g.seat = seat;
    int path[40], taken[40];
    for (int cell = 0; cell < 64; cell++) {
        if (owner(cells[cell]) == seat) {
            path[0] = cell;
            g.visit(cell, cells[cell], path, 1, taken, 0);
        }
    }
    if (g.count) {
        int best = 0;
        for (int i = 0; i < g.count; i++) best = std::max(best, (int)g.out[i * REC + 1]);
        int k = 0;
        for (int i = 0; i < g.count; i++) {
            if (g.out[i * REC + 1] == best) {
                if (k != i) std::memcpy(g.out + k * REC, g.out + i * REC, REC);
                k++;
            }
        }
        std::memcpy(out, g.out, (size_t)k * REC);
        return k;
    }
    int n = 0;
    for (int cell = 0; cell < 64; cell++) {
        int piece = cells[cell];
        if (owner(piece) != seat) continue;
        for (int d = 0; d < 4; d++) {
            if (!is_king(piece) && DR[d] != (seat == 0 ? -1 : 1)) continue;
            int to = stepc(cell, DR[d], DC[d]);
            while (to >= 0 && cells[to] == 0) {
                if (n < MAXMOVES) {
                    i8* rec = out + n * REC;
                    std::memset(rec, 0, REC);
                    rec[0] = 2;
                    rec[1] = 0;
                    rec[2] = (i8)cell;
                    rec[3] = (i8)to;
                    n++;
                }
                if (!is_king(piece)) break;
                to = stepc(to, DR[d], DC[d]);
            }
        }
    }
    return n;
}

int dames_record_size() { return REC; }
}

// ---------------------------------------------------------------------------------------------------------------------------------
// Recherche alpha-bêta. mode 0 : copie fidèle du bot de multi (mêmes évaluation, profondeurs, budget de nœuds, ordre des coups) ;
// mode 1 : version renforcée (table de transposition, extension des prises, évaluation enrichie).
namespace search {
using namespace std;
typedef uint64_t u64;
const int INF = 1000000;
struct Pos { i8 cells[64]; int next; int quiet; };

inline void apply_move(const Pos& p, const i8* rec, Pos& q) {
    std::memcpy(q.cells, p.cells, 64);
    int plen = rec[0], ncaps = rec[1];
    int piece = q.cells[(int)rec[2]];
    bool king_start = is_king(piece);
    q.cells[(int)rec[2]] = 0;
    for (int i = 1; i < plen; i++) piece = crown(piece, rec[2 + i]);
    for (int i = 0; i < ncaps; i++) q.cells[(int)rec[35 + i]] = 0;
    q.cells[(int)rec[2 + plen - 1]] = (i8)piece;
    q.next = 1 - p.next;
    q.quiet = (ncaps || !king_start) ? 0 : p.quiet + 1;
}

int eval_multi(const i8* cells, int seat) {
    double value = 0;
    for (int cell = 0; cell < 64; cell++) {
        int piece = cells[cell], side = owner(piece);
        if (side < 0) continue;
        int r = cell / 8, c = cell % 8;
        int adv = side == 0 ? 7 - r : r;
        double center = 7 - fabs(3.5 - c) - fabs(3.5 - r);
        value += (side == seat ? 1 : -1) * ((is_king(piece) ? 300 : 100 + adv * 5) + center * 3 + ((c == 0 || c == 7) ? 7 : 0));
    }
    return (int)value;
}

int eval_strong(const i8* cells, int seat) {
    int value = 0, men[2] = {0, 0}, kings[2] = {0, 0};
    for (int cell = 0; cell < 64; cell++) {
        int piece = cells[cell], side = owner(piece);
        if (side < 0) continue;
        int r = cell / 8, c = cell % 8, sgn = side == seat ? 1 : -1;
        int adv = side == 0 ? 7 - r : r;
        int v;
        if (is_king(piece)) { v = 330 + (int)(6 - fabs(3.5 - c) - fabs(3.5 - r)) * 3; kings[side]++; }
        else {
            v = 100 + adv * adv * 2 + ((c == 0 || c == 7) ? -3 : 3);
            if ((side == 0 && r == 7) || (side == 1 && r == 0)) v += 12;  // pion de dernière rangée : garde la promotion adverse
            men[side]++;
        }
        value += sgn * v;
    }
    // Avantage matériel : plus il y a de matériel d'écart, plus échanger est bon.
    int mine = men[seat] + 3 * kings[seat], theirs = men[1 - seat] + 3 * kings[1 - seat];
    if (mine + theirs) value += (mine - theirs) * 40 / (mine + theirs) * 3;
    return value;
}

struct TT { u64 key; int16_t value; i8 depth; i8 flag; };
TT* tt = nullptr;
const size_t TT_SIZE = 1 << 20;
u64 zob[5][64];
u64 zob_side;
bool zob_ready = false;
void init_zob() {
    if (zob_ready) return;
    u64 x = 88172645463325252ULL;
    auto next = [&]() { x ^= x << 13; x ^= x >> 7; x ^= x << 17; return x; };
    for (int p = 0; p < 5; p++) for (int c = 0; c < 64; c++) zob[p][c] = next();
    zob_side = next();
    tt = new TT[TT_SIZE]();
    zob_ready = true;
}
u64 hash_of(const Pos& p) {
    u64 h = p.next ? zob_side : 0;
    for (int c = 0; c < 64; c++) if (p.cells[c]) h ^= zob[(int)p.cells[c]][c];
    return h ^ ((u64)p.quiet * 0x9E3779B97F4A7C15ULL);
}

struct Ctx { int mode; long long nodes = 0, budget; bool exhausted = false; };

int negamax(Ctx& cx, const Pos& p, int depth, int alpha, int beta, int ply) {
    if (++cx.nodes > cx.budget) { cx.exhausted = true; return 0; }
    static i8 pool[64][MAXMOVES * REC];  // un tampon de coups par profondeur (évite une grosse pile)
    if (ply >= 63) return cx.mode == 0 ? eval_multi(p.cells, p.next) : eval_strong(p.cells, p.next);
    i8* moves = pool[ply];
    int n = dames_moves(p.cells, p.next, moves);
    if (n == 0) return -100000 + ply;
    if (p.quiet >= 20) return 0;
    bool capture = moves[1] > 0;
    if (depth <= 0 && !(cx.mode == 1 && capture && ply < 40)) return cx.mode == 0 ? eval_multi(p.cells, p.next) : eval_strong(p.cells, p.next);
    u64 h = 0;
    int a0 = alpha;
    if (cx.mode == 1) {
        h = hash_of(p);
        TT& e = tt[h % TT_SIZE];
        if (e.key == h && e.depth >= depth) {
            if (e.flag == 0) return e.value;
            if (e.flag == 1) alpha = max(alpha, (int)e.value); else beta = min(beta, (int)e.value);
            if (alpha >= beta) return e.value;
        }
    }
    int best = -INF;
    for (int i = 0; i < n; i++) {
        Pos q;
        apply_move(p, moves + i * REC, q);
        int v = -negamax(cx, q, depth - 1, -beta, -alpha, ply + 1);
        if (cx.exhausted) return 0;
        best = max(best, v);
        alpha = max(alpha, v);
        if (alpha >= beta) break;
    }
    if (cx.mode == 1) {
        TT& e = tt[h % TT_SIZE];
        e.key = h; e.depth = (i8)max(depth, 0); e.value = (int16_t)max(-30000, min(30000, best));
        e.flag = best <= a0 ? 2 : best >= beta ? 1 : 0;
    }
    return best;
}
}  // namespace search

extern "C" {
// Choisit un coup pour `seat`. Renvoie l'indice du coup dans la liste de dames_moves (-1 s'il n'y en a pas) ; *score reçoit l'évaluation.
int dames_search(const i8* cells, int seat, int quiet, int max_depth, long long budget, int mode, int* score) {
    using namespace search;
    init_zob();
    static i8 moves[MAXMOVES * REC];
    int n = dames_moves(cells, seat, moves);
    if (n == 0) return -1;
    Pos root;
    std::memcpy(root.cells, cells, 64);
    root.next = seat;
    root.quiet = quiet;
    Ctx cx;
    cx.mode = mode;
    cx.budget = budget;
    int chosen = 0, chosen_score = 0;
    for (int depth = 1; depth <= max_depth; depth++) {
        int best = -INF, cand = chosen;
        int order[MAXMOVES];
        order[0] = chosen;
        int k = 1;
        for (int i = 0; i < n; i++) if (i != chosen) order[k++] = i;
        for (int j = 0; j < n; j++) {
            Pos q;
            apply_move(root, moves + order[j] * REC, q);
            int v = -negamax(cx, q, depth - 1, -INF, -best, 1);
            if (cx.exhausted) break;
            if (v > best) { best = v; cand = order[j]; }
        }
        if (cx.exhausted) break;
        chosen = cand;
        chosen_score = best;
        if (best > 90000) break;
    }
    *score = chosen_score;
    return chosen;
}
}
