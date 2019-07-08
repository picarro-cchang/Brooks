// Uses timer1 to create periodic interrupts

// Set the period between metronome interrupts (ms)
#define METRONOME_PERIOD_MS 10

void metronome_init(void);

// Tasks for testing the scheduler
void test_task(void);

void offset_task(void);
