#include <stdio.h>

static unsigned retry_delay_ms(unsigned attempt, int enabled)
{
    if (!enabled)
        return 0;

    if (attempt > 6)
        attempt = 6;

    unsigned delay = 250 + 150 * attempt;
    return delay > 1000 ? 1000 : delay;
}

int main(void)
{
    printf("%u %u %u %u\n",
           retry_delay_ms(0, 1),
           retry_delay_ms(5, 1),
           retry_delay_ms(8, 1),
           retry_delay_ms(8, 0));
    return 0;
}
