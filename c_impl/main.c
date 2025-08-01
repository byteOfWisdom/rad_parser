#include "stdio.h"
#include "stdlib.h"
#include "stdint.h"


#pragma pack(push, 1)
typedef struct{
	uint32_t time;
	float value;
	unsigned char unit[8];
	int32_t alarm;
	uint32_t status;
	uint32_t intervall;
	unsigned char date[6];
	uint8_t delim;
	unsigned char time_string[6];
	uint8_t delim2;
	uint16_t filler;
} data_point;
#pragma pack(pop)

int main(int argc, char* argv[]) {
	if (argc < 2) {
		printf("no file to parse provided. exiting...\n");
		exit(1);
	}

	FILE* source = fopen(argv[1], "r");

	if (source == NULL) {
		printf("failed to open file. exiting...\n");
		exit(1);
	}

	uint8_t buff[44];
	printf("time; value; unit; alarm; status; intervall; date; time_string; filler\n");
	while (fread(buff, 44, 1, source) == 1) {
		data_point* dp = (data_point*) buff;
		dp->delim = 0;
		dp->delim2 = 0;
		printf(
			"%i; %f; %s; %i; 0x%0x4; %i; %s; %s; 0x%0x2\n",
			dp->time, dp->value, dp->unit,
			dp->alarm, dp->status, dp->intervall,
			dp->date, dp->time_string, dp->filler
		);
	}
	return 0;
}
