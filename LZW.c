/*
 ============================================================================
 Name        : LZW.c
 Author      : Dillan
 Version     : 1.0
 Description : LZW encoder / decoder for Seng 265
 ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BITS 12
#define MAX_CODE ( ( 1 << BITS ) - 1 )

#define DICTSIZE 4096                     /* allow 4096 entries in the dict  */
#define ENTRYSIZE 32
#define FIRST_CODE 256
#define END_CODE 255
#define UNUSED -1

#define MAX_FILENAME 100
#define MAX_SIZE 41

/*
 * This is the data structure for my dictionary.
 */
struct dictionary {
	int value;
	int parent;
	char character;
} dict[DICTSIZE];

char decodeStack[DICTSIZE];

/* Prototypes */
void encode(FILE*, FILE*);
void decode(FILE*, FILE*);

unsigned int findChild(int, int);
unsigned int decodeString(unsigned int, unsigned int);

/* Provided functions */
int read12(FILE *infil);
int write12(FILE *outfil, int int12);
void strip_lzw_ext(char *fname);
void flush12(FILE *outfil);

int main(int argc, char *argv[]) {
	/* File used for encoding or decoding */
	FILE *inputFile;

	/* File used to output the encoded data */
	FILE *outputFile;

	/*
	 * Check if the arguments passed in are correct
	 */
	if (argc == 3 && (*argv[2] == 'e' || *argv[2] == 'd')) {
		char mode = *argv[2];
		char fileName[MAX_FILENAME];

		/* Copy the argument into the fileName */
		strcpy(fileName, argv[1]);

		inputFile = fopen(fileName, "r");
		/* Check if there is no valid file name */
		if (inputFile == 0) {
			printf("Read error: file not found or cannot be read");
			exit(2);
		}		

		/* Check if can encode, then encode the line */
		if (mode == 'e') {
			outputFile = fopen(strcat(fileName, ".LZW"), "w");
			encode(inputFile, outputFile);
		}

		/* Check if can decode, then decode the line */
		else if (mode == 'd') {
			strip_lzw_ext(fileName);
			outputFile = fopen(fileName, "w");
			decode(inputFile, outputFile);
		}

	} else {
		printf("Invalid Usage, expected: RLE {filename} [e|d]");
		exit(4);
	}

	fclose(inputFile);
	fclose(outputFile);
	return 0;
}

void encode(FILE *in, FILE *out) {
	int nextCode;
	int character;
	int stringCode;
	unsigned int index;
	unsigned int i;
	nextCode = FIRST_CODE;

	/* Put unused values into the dictionary */
	for (i = 0; i < DICTSIZE; i++) {
		dict[i].value = UNUSED;
	}

	if ((stringCode = fgetc(in)) == EOF)
		stringCode = END_CODE;

	/* loop through the file until reaches the EOF */
	while ((character = fgetc(in)) != -1) {
		index = findChild(stringCode, character);

		if (dict[index].value != -1)
			stringCode = dict[index].value;
		else {
			if (nextCode <= MAX_CODE) {
				dict[index].value = nextCode++;
				dict[index].parent = stringCode;
				dict[index].character = (char) character;
			}
			//output the code
			write12(out, (unsigned long) stringCode);
			stringCode = character;
		}
	}
	write12(out, (unsigned long)stringCode);
	flush12(out);
	write12(out, (unsigned long) END_CODE);
}

void decode(FILE *in, FILE *out) {
	unsigned int nextCode;
	unsigned int newCode;
	unsigned int oldCode;
	int character;
	unsigned int count;
	nextCode = FIRST_CODE;
	oldCode = (unsigned int) read12(in);
	if (oldCode == -1)
		return;

	character = oldCode;
	putc(oldCode, out);

	while ((newCode = (unsigned int) read12(in)) != EOF) {
		if (newCode >= nextCode) {
			decodeStack[0] = (char) character;
			count = decodeString(1, oldCode);
		} else
			count = decodeString(0, newCode);

		character = decodeStack[count - 1];

		while (count > 0) {
			putc(decodeStack[--count], out);
			fflush(out);
		}

		if (nextCode <= MAX_CODE) {
			dict[nextCode].parent = oldCode;
			dict[nextCode].character = (char) character;
			nextCode++;
		}

		oldCode = newCode;

	}

}

unsigned int findChild(int parentCode, int childChar) {
	int index;
	int offset;

	index = (childChar << (BITS - 8)) ^ parentCode;

	if (index == 0)
		offset = 1;
	else
		offset = DICTSIZE - index;

	while (1) {
		if (dict[index].value == UNUSED)
			return index;

		if (dict[index].parent == parentCode
				&& dict[index].character == (char) childChar)
			return index;

		index -= offset;

		if (index < 0)
			index += DICTSIZE;
	}
}

unsigned int decodeString(unsigned int count, unsigned int code) {
	while (code > 255) {
		decodeStack[count++] = dict[code].character;

		code = dict[code].parent;
	}

	decodeStack[count++] = (char) code;
	return count;
}

/*****************************************************************************/
/* read12() handles the complexities of reading 12 bit numbers from a file.  */
/* It is the simple counterpart of write12(). Like write12(), read12() uses  */
/* static variables. The function reads two 12 bit numbers at a time, but    */
/* only returns one of them. It stores the second in a static variable to be */
/* returned the next time read12() is called.                                */
int read12(FILE *infil) {
	static int number1 = -1, number2 = -1;
	unsigned char hi8, lo4hi4, lo8;
	int retval;

	if (number2 != -1) /* there is a stored number from   */
	{ /* last call to read12() so just   */
		retval = number2; /* return the number without doing */
		number2 = -1; /* any reading                     */
	} else /* if there is no number stored    */
	{
		if (fread(&hi8, 1, 1, infil) != 1) /* read three bytes (2 12 bit nums)*/
			return (-1);
		if (fread(&lo4hi4, 1, 1, infil) != 1)
			return (-1);
		if (fread(&lo8, 1, 1, infil) != 1)
			return (-1);

		number1 = hi8 * 0x10; /* move hi8 4 bits left            */
		number1 = number1 + (lo4hi4 / 0x10); /* add hi 4 bits of middle byte    */

		number2 = (lo4hi4 % 0x10) * 0x0100; /* move lo 4 bits of middle byte   */
		/* 8 bits to the left              */
		number2 = number2 + lo8; /* add lo byte                     */

		retval = number1;
	}
	return (retval);
}

/*****************************************************************************/
/* write12() handles the complexities of writing 12 bit numbers to file so I */
/* don't have to mess up the LZW algorithm. It uses "static" variables. In a */
/* C function, if a variable is declared static, it remembers its value from */
/* one call to the next. You could use global variables to do the same thing */
/* but it wouldn't be quite as clean. Here's how the function works: it has  */
/* two static integers: number1 and number2 which are set to -1 if they do   */
/* not contain a number waiting to be written. When the function is called   */
/* with an integer to write, if there are no numbers already waiting to be   */
/* written, it simply stores the number in number1 and returns. If there is  */
/* a number waiting to be written, the function writes out the number that   */
/* is waiting and the new number as two 12 bit numbers (3 bytes total).      */
int write12(FILE *outfil, int int12) {
	static int number1 = -1, number2 = -1;
	unsigned char hi8, lo4hi4, lo8;
	unsigned long bignum;

	if (number1 == -1) /* no numbers waiting             */
	{
		number1 = int12; /* save the number for next time  */
		return (0); /* actually wrote 0 bytes         */
	}

	if (int12 == -1) /* flush the last number and put  */
		number2 = 0x0FFF; /* padding at end                 */
	else
		number2 = int12;

	bignum = number1 * 0x1000; /* move number1 12 bits left      */
	bignum = bignum + number2; /* put number2 in lower 12 bits   */

	hi8 = (unsigned char) (bignum / 0x10000); /* bits 16-23 */
	lo4hi4 = (unsigned char) ((bignum % 0x10000) / 0x0100); /* bits  8-15 */
	lo8 = (unsigned char) (bignum % 0x0100); /* bits  0-7  */

	fwrite(&hi8, 1, 1, outfil); /* write the bytes one at a time  */
	fwrite(&lo4hi4, 1, 1, outfil);
	fwrite(&lo8, 1, 1, outfil);

	number1 = -1; /* no bytes waiting any more      */
	number2 = -1;

	return (3); /* wrote 3 bytes                  */
}

/** Write out the remaining partial codes */
void flush12(FILE *outfil) {
	write12(outfil, -1); /* -1 tells write12() to write    */
} /* the number in waiting          */

/** Remove the ".LZW" extension from a filename */
void strip_lzw_ext(char *fname) {
	char *end = fname + strlen(fname);

	while (end > fname && *end != '.' && *end != '\\' && *end != '/') {
		--end;
	}
	if ((end > fname && *end == '.')
			&& (*(end - 1) != '\\' && *(end - 1) != '/')) {
		*end = '\0';
	}
}
