from __future__ import annotations

import os
import pandas as pd

from Bio import AlignIO


class AlignmentFasta:

    def __init__(self, sequences: dict) -> None:
        """
        Initializer for the an alignment that is imported/ exported as a fasta file.

        Parameters
        ----------
        sequences : dict
            The dictionary that contains the sequences of the alignment. The key is the header of the fasta file and the
             value is the sequence, it may contain gaps and other characters that are given by MEGAN.
        """
        self.sequences = sequences
        self.seq_length = len(list(sequences.values())[0])
        self.num_of_sequences = len(sequences)

    @staticmethod
    def __fix_header_spaces(path: str) -> None:
        """
        This private function replaces all spaces that are in the header string. This needs to be done, because
        otherwise the function AlignIO.read() from the Biopython package will read in the header until the first space
        is encountered. This may lead to conflicting header/ keys for the alignment dictionary.

        Parameters
        ----------
        path : str
            Path to the fasta file that will be modified.

        Returns
        -------
        None
        """
        # get all lines from the file
        with open(path, 'r') as file:
            lines = file.readlines()

        # replace spaces in the header, the sequence lines will not be modified
        lines = [line.replace(' ', '_') if line.startswith('>') else line for line in lines]

        # write lines to the file
        with open(path, 'w') as file:
            file.writelines(lines)

    @staticmethod
    def read_file(path: str) -> AlignmentFasta:
        """
        Function to read in a fasta file. The given path has to lead to a file that ends either with '.fa' or with
        '.fasta'. The read in fasta alignment will be returned as an AlignmentFasta instance.

        Recommended use:

        alignment = AlignmentFasta.read([path_to_fasta])

        Parameters
        ----------
        path : str
            The path for the file that will be read. The given file must end with either '.fa' or '.fasta'.

        Returns
        -------
        An AlignmentFasta instance that contains the read alignment data.
        """
        assert path.endswith('.fa') or path.endswith('.fasta'), 'Cannot read a non Fasta file.'

        # replace the spaces in the header to get more precise ids
        AlignmentFasta.__fix_header_spaces(path)

        with open(path, 'r') as file:
            # use of Biopython's implementation, because it is more efficient
            alignment = AlignIO.read(file, 'fasta')

            sequences_dict = {}

            # iterate over each line of the alignment object and add it to our dictionary
            for record in alignment:
                sequences_dict[record.id] = str(record.seq)

        return AlignmentFasta(sequences_dict)  # generate and return an instance of AlignmentFasta

    @staticmethod
    def read_directory(path: str) -> list[AlignmentFasta]:
        """
        Function to read in multiple fasta files in a directory. Internally just reads in every file individually. Other
        file types that are in the directory are skipped.

        Note:   If we encounter bigger directories, we need to implement a iterator because otherwise we will encounter
                issues with memory.

        Parameters
        ----------
        path : str
            Path to a directory that contains the fasta files we want to read in. It can include other files.

        Returns
        -------
        A list of AlignmentFasta instances for each fasta file that is in the given directory.
        """

        assert os.path.isdir(path), 'Path is not a directory'  # assure that path is a directory

        align_list = []

        # iterate over all files in the directory and append the respective alignment to a list
        for filename in os.listdir(path):

            # if the file is not a fasta file, skip it
            if not (filename.endswith('.fa') or filename.endswith('.fasta')):
                continue

            align_list.append(AlignmentFasta.read_file(path + '\\' + filename))

        return align_list

    def write_file(self, path: str) -> None:
        """
        Function that writes the alignment, with which it is called, to a file at the given path. The given path must
        end either with '.fa' or with '.fasta'.

        Parameters
        ----------
        path : str
            The path for the file to which the alignment will be written. The given file must end with either '.fa' or
             '.fasta'.
        Returns
        -------
        None
        """
        assert path.endswith('.fa') or path.endswith('.fasta'), 'Can only write into a fasta file.'

        # check if the file already exists, if not create a new empty file
        if not os.path.isfile(path):
            with open(path, 'w') as _:
                pass

        # we now know that the file must be existing
        with open(path, 'w') as file:
            # iterate over all headers and their respective sequence
            for header, sequence in self.sequences.items():
                file.write(f'>{header}')

                '''Split the sequence into blocks of 60 characters to assure a better readability of the 
                generated fasta file.'''

                file.write('\n')
                file.write('\n'.join(sequence[i:i + 60] for i in range(0, len(sequence), 60)))
                file.write('\n')

    @staticmethod
    def preprocess_directory(path: str) -> None:
        """
        This function preprocesses all fasta files in the given directory.

        By preprocessing the deletion of columns with gaps is meant. All the processed fasta files will be stored in the
        directory called "processed". The filenames will be lost, because at this point we are just interested in the
        alignment and not in what it is.

        Parameters
        ----------
        path : str
            The path that contains all fasta files that should be processed. It must be a path for a directory. Other
            files in the directory will be ignored.

        Returns
        -------
        None
        """

        alignment_list = AlignmentFasta.read_directory(path)  # get all alignments from the directory

        folder_name = path.split('\\')[-1]  # get the name of the folder to know where the file came from

        # iterate over all alignments, delete their gaped columns and save them
        for index, alignment in enumerate(alignment_list):
            alignment.__delete_gaped_columns()
            alignment.write_file(f'processed\\{folder_name}_processed_{index}.fasta')

    def __delete_gaped_columns(self) -> None:
        """
        Private function that deletes all columns that contain a gap. For the operation a pandas dataframe is used,
        because it already implements certain functions in a time efficient way.

        Returns
        -------
        None
        """

        # transform the strings to lists of characters
        sequence_dict = self.sequences

        for key in sequence_dict.keys():
            sequence_dict[key] = list(sequence_dict[key])

        # work with a pandas dataframe to do certain actions fast
        seq_df = pd.DataFrame.from_dict(sequence_dict, orient='index')
        seq_df = seq_df.loc[:, ~(seq_df == '-').any()]  # delete all columns with a gap

        # convert the dataframe back to a dictionary of lists
        sequence_dict = seq_df.T.to_dict('list')

        # convert the dictionary of lists to a typical dictionary of strings
        for key in sequence_dict.keys():
            sequence_dict[key] = ''.join(sequence_dict[key])

        # fix the processed alignment
        self.sequences = sequence_dict


def main():
    AlignmentFasta.preprocess_directory('Data\\')
    return None


if __name__ == '__main__':
    main()
