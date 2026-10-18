// Moteur de Go 9x9 pour Garry Zero : captures, suicide interdit, ko simple, fin à deux passes, score de surface (Tromp-Taylor) avec komi.
// Un état = 86 octets : [0..80] plateau (0 vide, 1 noir, 2 blanc), [81] joueur au trait, [82] point de ko (255 = aucun),
// [83] passes consécutives, [84] nombre de coups, [85] dernier coup (81 = passe, 255 = aucun).
// Compilation : g++ -O2 -shared -o go9.dll go9.cpp
#include <cstdint>
#include <cstring>

namespace {
const int N = 9, NN = 81, W = 86, MAXMOVES = 160;
const float KOMI = 7.5f;
inline int nb_of(int p, int* out) {
    int r = p / N, c = p % N, k = 0;
    if (r > 0) out[k++] = p - N;
    if (r < N - 1) out[k++] = p + N;
    if (c > 0) out[k++] = p - 1;
    if (c < N - 1) out[k++] = p + 1;
    return k;
}
// Groupe de `p` ; remplit `members` et retourne le nombre de libertés (distinctes).
int flood(const uint8_t* b, int p, int* members, int& count) {
    uint8_t color = b[p];
    bool seen[NN] = {false}, lib[NN] = {false};
    int stack[NN], sp = 0, libs = 0;
    count = 0;
    stack[sp++] = p;
    seen[p] = true;
    while (sp) {
        int q = stack[--sp];
        members[count++] = q;
        int nb[4], k = nb_of(q, nb);
        for (int i = 0; i < k; i++) {
            int x = nb[i];
            if (b[x] == 0) {
                if (!lib[x]) { lib[x] = true; libs++; }
            } else if (b[x] == color && !seen[x]) {
                seen[x] = true;
                stack[sp++] = x;
            }
        }
    }
    return libs;
}
// Pose une pierre `color` en `p` sur une copie ; retourne -1 si illégal (occupé, ko, suicide), sinon le nombre de pierres capturées.
int try_move(const uint8_t* st, int p, uint8_t color, uint8_t* out_board, int* captured_point) {
    if (st[p] != 0 || st[82] == p) return -1;
    uint8_t b[NN];
    memcpy(b, st, NN);
    b[p] = color;
    int captured = 0, members[NN], cnt;
    int nb[4], k = nb_of(p, nb);
    for (int i = 0; i < k; i++) {
        int x = nb[i];
        if (b[x] == 3 - color) {
            int libs = flood(b, x, members, cnt);
            if (libs == 0) {
                for (int j = 0; j < cnt; j++) b[members[j]] = 0;
                captured += cnt;
                *captured_point = members[0];
            }
        }
    }
    if (flood(b, p, members, cnt) == 0) return -1;  // suicide
    memcpy(out_board, b, NN);
    return captured;
}
float area_margin(const uint8_t* b) {  // noir - blanc - komi
    int black = 0, white = 0;
    bool seen[NN] = {false};
    for (int p = 0; p < NN; p++) {
        if (b[p] == 1) black++;
        else if (b[p] == 2) white++;
        else if (!seen[p]) {
            int stack[NN], sp = 0, size = 0;
            bool touch_b = false, touch_w = false;
            stack[sp++] = p;
            seen[p] = true;
            while (sp) {
                int q = stack[--sp];
                size++;
                int nb[4], k = nb_of(q, nb);
                for (int i = 0; i < k; i++) {
                    int x = nb[i];
                    if (b[x] == 0) {
                        if (!seen[x]) { seen[x] = true; stack[sp++] = x; }
                    } else if (b[x] == 1) touch_b = true;
                    else touch_w = true;
                }
            }
            if (touch_b && !touch_w) black += size;
            else if (touch_w && !touch_b) white += size;
        }
    }
    return (float)black - (float)white - KOMI;
}
}  // namespace

extern "C" {
int go9_width() { return W; }

void go9_initial(uint8_t* st, int n) {
    memset(st, 0, (size_t)n * W);
    for (int i = 0; i < n; i++) { st[i * W + 81] = 1; st[i * W + 82] = 255; st[i * W + 85] = 255; }
}

// out : n x 82 (0/1). La passe (indice 81) est toujours légale.
void go9_legal(const uint8_t* states, int n, uint8_t* out) {
    for (int i = 0; i < n; i++) {
        const uint8_t* st = states + (size_t)i * W;
        uint8_t* o = out + (size_t)i * 82;
        uint8_t tmp[NN];
        int cp = 0;
        for (int p = 0; p < NN; p++) o[p] = try_move(st, p, st[81], tmp, &cp) >= 0 ? 1 : 0;
        o[81] = 1;
    }
}

// Applique actions[i] (0..80 point, 81 passe) à l'état i, en place. terminal[i] ; value[i] du point de vue du joueur désormais au trait.
void go9_step(uint8_t* states, const int* actions, int n, uint8_t* terminal, float* value) {
    for (int i = 0; i < n; i++) {
        uint8_t* st = states + (size_t)i * W;
        int a = actions[i];
        uint8_t color = st[81];
        st[82] = 255;
        if (a == 81) {
            st[83]++;
        } else {
            uint8_t nb_board[NN];
            int cp = -1;
            int captured = try_move(st, a, color, nb_board, &cp);
            if (captured < 0) {  // coup illégal : traité comme une passe (ne devrait pas arriver, le MCTS ne propose que des coups légaux)
                st[83]++;
                a = 81;
            } else {
                memcpy(st, nb_board, NN);
                st[83] = 0;
                if (captured == 1) {  // ko simple : une capture et une pierre isolée à une seule liberté
                    int members[NN], cnt;
                    int libs = flood(st, a, members, cnt);
                    if (cnt == 1 && libs == 1) st[82] = (uint8_t)cp;
                }
            }
        }
        st[84] = st[84] < 255 ? st[84] + 1 : 255;
        st[85] = (uint8_t)(a == 81 ? 81 : a);
        st[81] = 3 - color;
        bool over = st[83] >= 2 || st[84] >= MAXMOVES;
        terminal[i] = over ? 1 : 0;
        if (over) {
            float margin = area_margin(st);
            uint8_t winner = margin > 0 ? 1 : 2;
            value[i] = (st[81] == winner) ? 1.0f : -1.0f;
        } else {
            value[i] = 0.0f;
        }
    }
}

float go9_margin(const uint8_t* st) { return area_margin(st); }
}
