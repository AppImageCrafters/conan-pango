#include <pango/pango.h>

int main(int argc, char* argv[]) {
    PangoFontDescription* pfd = pango_font_description_new();
    if (!pfd) return 1;
    pango_font_description_set_size(pfd, 12);
    return 0;
}
